#!/bin/bash
# RSI 运行时入口。用法: run.sh <morning|evening|weekly|smoke>
# launchd 的 PATH 极简，须显式补全（claude 在 ~/.local/bin，lark-cli/gh 在 /opt/homebrew/bin）。
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

MODE="${1:-}"
case "$MODE" in
  morning|evening|weekly|smoke|selfcheck) ;;
  *) echo "用法: run.sh <morning|evening|weekly|smoke|selfcheck>" >&2; exit 2 ;;
esac

# 周日的晚场自动升级为周审（少一个 plist，少一个概念）
if [ "$MODE" = "evening" ] && [ "$(date +%u)" = "7" ]; then
  MODE="weekly"
fi

LOG="$ROOT/system/logs/${MODE}-$(date +%Y%m%d-%H%M%S).log"
LOCK="$ROOT/system/.lock"
TIMEOUT=2400
# 每场跑完在本地留一行运行记录，下一场开场必读。
# 为什么不能只靠飞书告警：2026-08-15 的 s3 与 pm 两场都因本机 DNS 中断而失败，
# 而告警渠道（飞书）与失败原因共享同一条依赖——网络一断，告警本身也发不出去，
# 故障 100% 静默，s3 干完的活留在工作区未提交、晚场整场蒸发都无人知晓（见 L-025）。
# 仓库文件 + 下一场的注入参数，是本系统唯一不依赖网络的告警信道。
RUNLOG="$ROOT/workspace/session-runs.log"
# 排班每 6 小时一场；超过此间隔没有任何运行记录，说明中间有场次根本没启动（关机/休眠/plist 掉了）
GAP_ALERT=$((7 * 3600))
# 前场持锁超过此时长即判定为挂死，本场强制接管（2026-08-14 s1 事故：13:30 场僵死 8h39m，
# 锁一直被持有，把 19:30 晚场的复盘/简报/push 整场吃掉。见 LEDGER L-017）
STALE_AFTER=$((TIMEOUT + 600))

notify() {
  "$ROOT/system/notify.sh" "$1" >>"$LOG" 2>&1 || true
}

# 本场收尾：把结果落到 RUNLOG。rc 之外还记两件下一场抢救时必须知道的事——
# journal 写没写（判定"活干了但没交付"），工作区脏不脏（判定"有没有未提交的成果要救"）。
# phase=start 在开场落、phase=end 在收尾落。为什么必须有 start：
# 只落 end 时，一场若在收尾前被硬杀（kill -9/断电/休眠）就什么都不留，末行仍是更早那场的记录，
# 于是下一场把"已经处理过的旧故障"重报一遍，同时真正的新丢场被完全掩盖。
# 2026-08-16 s2 实证：s1 跑在尚无 record_run 的旧版上（新代码只对下一场生效），一行未落，
# s2 开场因此收到 08-15 evening 的陈旧告警 + 假的"排班缺口 11 小时"（见 L-026）。
# 有了 start，"末行"恒等于"最近真正启动过的那一场"，两种情形才分得开。
record_run() {
  local rc="$1" jrn="${2:-none}" phase="${3:-end}" dirty jw
  dirty="$(git -C "$ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$jrn" != "none" ] && [ -f "$ROOT/$jrn" ]; then jw=1; else jw=0; fi
  printf '%s t=%s mode=%s phase=%s rc=%s journal=%s journal_written=%s dirty=%s log=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(date +%s)" "$MODE" "$phase" "$rc" "$jrn" "$jw" "${dirty:-0}" "${LOG#$ROOT/}" \
    >>"$RUNLOG" 2>/dev/null || true
}

# 开场自检：上一场是否异常（非零退出 / 活干了没写 journal / 排班缺口）。
# 有异常则输出一段文字，由调用方注入本场 PROMPT；无异常输出空。
session_alert() {
  [ -s "$RUNLOG" ] || return 0
  local last rc jw dirty dirty_now ts jrn phase gap alerts=""
  last="$(tail -n 1 "$RUNLOG")"
  rc="$(printf '%s' "$last"    | sed -n 's/.* rc=\([0-9-]*\) .*/\1/p')"
  jw="$(printf '%s' "$last"    | sed -n 's/.*journal_written=\([0-9]*\).*/\1/p')"
  dirty="$(printf '%s' "$last" | sed -n 's/.* dirty=\([0-9]*\).*/\1/p')"
  ts="$(printf '%s' "$last"    | sed -n 's/.* t=\([0-9]*\) .*/\1/p')"
  jrn="$(printf '%s' "$last"   | sed -n 's/.* journal=\([^ ]*\).*/\1/p')"
  phase="$(printf '%s' "$last" | sed -n 's/.* phase=\([a-z]*\) .*/\1/p')"
  gap=$(( $(date +%s) - ${ts:-0} ))
  # dirty 是"上一场结束当时"的快照，不等于现在还脏——后续场次可能已抢救并提交。
  # 只有现在仍然脏，才值得让本场停下来先抢救；否则如实说明已被处置，不重复报警。
  dirty_now="$(git -C "$ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"

  # 末行是 start 且不是本场自己 = 那一场开了场却没能收尾（被硬杀/断电/休眠），属硬丢场
  [ "${phase:-end}" = "start" ] && alerts="${alerts}
- **上一场只开场未收尾**（记录停在 \`phase=start\`）：run.sh 进程被硬杀（kill -9／断电／休眠），连退出码都没留下。查 \`${last##*log=}\` 的最后一行确认它干到哪一步，未提交的成果按下一条处理。"

  [ "${rc:-0}" != "0" ] && alerts="${alerts}
- **上一场非零退出**（rc=${rc}）：先读它的日志尾部（\`${last##*log=}\`）判断是崩在哪一步。"
  [ "${jw:-1}" != "1" ] && alerts="${alerts}
- **上一场没写 journal**（应写 \`${jrn}\`）：活可能干了一半就崩了，属丢场，必须补记（标明是本场追认）并在 LEDGER 记一条。"
  if [ "${dirty:-0}" != "0" ] && [ "${dirty_now:-0}" != "0" ]; then alerts="${alerts}
- **上一场结束时工作区有 ${dirty} 处未提交改动，且现在仍有 ${dirty_now} 处**：先 \`git status\` + \`git diff\` 看清那是不是上一场没来得及交付的成果，**先抢救再干新活**；确认无用才丢弃。"
  elif [ "${dirty:-0}" != "0" ]; then alerts="${alerts}
- （上一场遗留的 ${dirty} 处改动**现已提交，无需抢救**——工作区当前 clean，此条仅作说明。）"
  fi
  [ -n "${ts:-}" ] && [ "$gap" -gt "$GAP_ALERT" ] && alerts="${alerts}
- **排班缺口 $((gap / 3600)) 小时**（上一条运行记录到现在，正常应 ≤6 小时）：中间有场次根本没启动（关机/休眠/plist 失效），核对 \`launchctl list | grep rsi\` 并在 journal 记明丢了几场。"

  [ -n "$alerts" ] || return 0
  printf '%s' "
## ⚠️ 上一场健康自检（run.sh 自动注入，优先于本场原定计划）

上一条运行记录：\`${last}\`
${alerts}

**处理完这些再开始本场的正常流程**；若判定无需处理，也要在 journal 写明判断依据。"
}

if [ "$MODE" = "selfcheck" ]; then
  out="$(session_alert)"
  if [ -n "$out" ]; then printf '%s\n' "$out"; exit 1; else echo "✓ 上一场运行记录正常"; exit 0; fi
fi

# mkdir 锁 + 陈旧锁检测（macOS 无 flock）
# 判活不只看 pid 存在，还看持锁时长：pid 活着但超过 STALE_AFTER 属"挂死"，必须强制接管，
# 否则一场僵死会把它之后的每一场都挡在门外（无限连锁，而非只损失一场）。
take_lock() { mkdir "$LOCK" 2>/dev/null && echo $$ >"$LOCK/pid" && date +%s >"$LOCK/start"; }

acquire_lock() {
  take_lock && return 0
  local oldpid oldstart age
  oldpid="$(cat "$LOCK/pid" 2>/dev/null || true)"
  oldstart="$(cat "$LOCK/start" 2>/dev/null || echo 0)"
  age=$(( $(date +%s) - oldstart ))

  # 先按时间判断，再按进程判断。顺序不能反：锁目录建好到 pid 落盘之间有竞态窗口，
  # 此时 pid 读出来是空的，若先按进程判断就会把一个刚起步的正常前场误判成陈旧锁夺走。
  if [ "$oldstart" -gt 0 ] && [ "$age" -le "$STALE_AFTER" ]; then
    echo "另一场会话运行中(pid=${oldpid:-?}, 已运行 ${age}s)，本场退出" >>"$LOG"
    return 1
  fi

  # 锁已超期（oldstart=0 则是无时间戳的旧格式锁，退化为原来的纯 pid 判断）
  if [ -n "$oldpid" ] && kill -0 "$oldpid" 2>/dev/null; then
    echo "前场超期未退(pid=$oldpid, 已运行 ${age}s > ${STALE_AFTER}s)，强制接管" >>"$LOG"
    notify "⚠️ **RSI 前场会话挂死已被接管**：pid=$oldpid 持锁 ${age}s（阈值 ${STALE_AFTER}s），本场（${MODE}）已终止它并继续。请留意上一场是否留下未提交的改动。"
    kill -TERM "$oldpid" 2>/dev/null || true
    sleep 5
    kill -KILL "$oldpid" 2>/dev/null || true
    sleep 1   # 等旧进程的 EXIT trap 删完锁，再建新锁，否则新锁会被它顺手删掉
  else
    echo "清理陈旧锁(pid=${oldpid:-?})" >>"$LOG"
  fi
  rm -rf "$LOCK"
  take_lock
}

acquire_lock || exit 0
trap 'rm -rf "$LOCK"' EXIT
# 被外部终止（launchctl 操作/关机）时先告警再退出——2026-08-11 事故曾静默死亡
trap 'record_run 143 "${JOURNAL:-none}"; notify "⚠️ **RSI ${MODE} 场会话被外部终止**（SIGTERM）。若非人为关机，请检查是否有会话违反调度自保禁令。日志：${LOG#$ROOT/}"; exit 143' TERM

echo "=== RSI $MODE 场 $(date '+%F %T') ===" >>"$LOG"

# 会话开始前自动收取飞书新指令进 INBOX（失败不阻断会话）
if [ "$MODE" != "smoke" ]; then
  python3 "$ROOT/system/pull_inbox.py" >>"$LOG" 2>&1 || true
fi

if [ "$MODE" = "smoke" ]; then
  PROMPT="这是 RSI 系统链路冒烟测试。只回复两个字：正常。不要执行任何其他操作。"
else
  # 排班：每 6 小时一场（人 2026-08-10 21:53 飞书指令）。01:30/07:30/13:30 走工作场协议，
  # 19:30 走晚场收尾协议。同一天有 3 场工作会话，journal 文件名须按场次区分否则互相覆盖。
  # 协议文件属法律层不可改，故场次参数在此以"运行时参数"注入，正文默认值以注入值为准。
  TODAY="$(date +%F)"
  HOUR="$(date +%H)"; HOUR="${HOUR#0}"
  if [ "$MODE" = "morning" ]; then
    if [ "$HOUR" -lt 6 ]; then SLOT="s1"; elif [ "$HOUR" -lt 12 ]; then SLOT="s2"; else SLOT="s3"; fi
    JOURNAL="journal/${TODAY}-${SLOT}.md"
  else
    JOURNAL="journal/${TODAY}-pm.md"
  fi
  PROMPT="$(cat "$ROOT/system/prompts/$MODE.md")

---

# 本场运行时参数（由 run.sh 注入，优先于协议正文中的默认值）

- **排班**：每 6 小时一场。当日 01:30 / 07:30 / 13:30 走工作场协议（morning.md），19:30 走晚场收尾协议（evening.md，含复盘/简报/push；周日自动升级周审）。
- **本场 journal 文件名**：\`${JOURNAL}\`。协议正文里写的默认文件名（-am.md）以此为准替换。
- **恢复上下文时**：先读今天已有的工作场 journal（\`journal/${TODAY}-s1.md\` / \`-s2.md\` / \`-s3.md\`，存在哪些取决于今天已跑过几场），再读最近一份 \`-pm.md\`。同一天后面的场次要接着前面的场次干，不要重做已完成的事。
- **会话预算仍为约 30 分钟**：场次变密不等于单场可以摊大饼，宁可少领任务保证闭环。
$(session_alert)"
fi

# 超时看门狗（macOS 无 GNU timeout）。
# 不用 perl alarm：alarm 走的是内核定时器，Mac 合盖睡眠期间不推进——2026-08-13 13:30 场因此
# 僵死 8h39m 才被 TIMEOUT=2400 杀掉（见 LEDGER L-017）。改为每分钟比较一次 date +%s 绝对时间戳，
# 睡眠期间真实时间照走，机器一醒来就立刻判超时。
# 开场记录必须落在 session_alert 之后（上面构造 PROMPT 时已调用），否则它会读到本场自己这一行
[ "$MODE" != "smoke" ] && record_run 0 "${JOURNAL:-none}" start

START="$(date +%s)"
claude -p "$PROMPT" --dangerously-skip-permissions >>"$LOG" 2>&1 &
CLAUDE_PID=$!
(
  while kill -0 "$CLAUDE_PID" 2>/dev/null; do
    sleep 60
    if [ $(( $(date +%s) - START )) -gt "$TIMEOUT" ]; then
      : >"$LOCK/timeout"
      kill -TERM "$CLAUDE_PID" 2>/dev/null || true
      sleep 10
      kill -KILL "$CLAUDE_PID" 2>/dev/null || true
      break
    fi
  done
) &
WATCHDOG_PID=$!
wait "$CLAUDE_PID"
RC=$?
kill "$WATCHDOG_PID" 2>/dev/null || true
# 看门狗留下的标记优先于被杀进程的退出码，保持"142 = 超时"的告警语义
[ -f "$LOCK/timeout" ] && RC=142

echo "=== 退出码 $RC $(date '+%F %T') ===" >>"$LOG"

# 先落本地运行记录，再发飞书告警：网络故障时后者必然失败，前者是下一场唯一能看到的信号
[ "$MODE" != "smoke" ] && record_run "$RC" "${JOURNAL:-none}"

if [ "$RC" -ne 0 ]; then
  if [ "$RC" -eq 142 ]; then
    REASON="超时(${TIMEOUT}s 被强制终止)"
  else
    REASON="异常退出(exit=$RC)"
  fi
  notify "⚠️ **RSI ${MODE} 场会话失败**：${REASON}
日志：\`${LOG#$ROOT/}\`（尾部摘录）
\`\`\`
$(tail -c 800 "$LOG")
\`\`\`"
fi

exit "$RC"
