#!/bin/bash
# RSI 运行时入口。用法: run.sh <morning|evening|weekly|smoke>
# launchd 的 PATH 极简，须显式补全（claude 在 ~/.local/bin，lark-cli/gh 在 /opt/homebrew/bin）。
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

MODE="${1:-}"
case "$MODE" in
  morning|evening|weekly|smoke) ;;
  *) echo "用法: run.sh <morning|evening|weekly|smoke>" >&2; exit 2 ;;
esac

# 周日的晚场自动升级为周审（少一个 plist，少一个概念）
if [ "$MODE" = "evening" ] && [ "$(date +%u)" = "7" ]; then
  MODE="weekly"
fi

LOG="$ROOT/system/logs/${MODE}-$(date +%Y%m%d-%H%M%S).log"
LOCK="$ROOT/system/.lock"
TIMEOUT=2400
# 前场持锁超过此时长即判定为挂死，本场强制接管（2026-08-14 s1 事故：13:30 场僵死 8h39m，
# 锁一直被持有，把 19:30 晚场的复盘/简报/push 整场吃掉。见 LEDGER L-017）
STALE_AFTER=$((TIMEOUT + 600))

notify() {
  "$ROOT/system/notify.sh" "$1" >>"$LOG" 2>&1 || true
}

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
trap 'notify "⚠️ **RSI ${MODE} 场会话被外部终止**（SIGTERM）。若非人为关机，请检查是否有会话违反调度自保禁令。日志：${LOG#$ROOT/}"; exit 143' TERM

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
- **会话预算仍为约 30 分钟**：场次变密不等于单场可以摊大饼，宁可少领任务保证闭环。"
fi

# 超时看门狗（macOS 无 GNU timeout）。
# 不用 perl alarm：alarm 走的是内核定时器，Mac 合盖睡眠期间不推进——2026-08-13 13:30 场因此
# 僵死 8h39m 才被 TIMEOUT=2400 杀掉（见 LEDGER L-017）。改为每分钟比较一次 date +%s 绝对时间戳，
# 睡眠期间真实时间照走，机器一醒来就立刻判超时。
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
