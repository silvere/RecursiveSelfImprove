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

notify() {
  "$ROOT/system/notify.sh" "$1" >>"$LOG" 2>&1 || true
}

# mkdir 锁 + 陈旧锁检测（macOS 无 flock）
acquire_lock() {
  if mkdir "$LOCK" 2>/dev/null; then
    echo $$ >"$LOCK/pid"
    return 0
  fi
  local oldpid
  oldpid="$(cat "$LOCK/pid" 2>/dev/null || true)"
  if [ -n "$oldpid" ] && kill -0 "$oldpid" 2>/dev/null; then
    echo "另一场会话运行中(pid=$oldpid)，本场退出" >>"$LOG"
    return 1
  fi
  echo "清理陈旧锁(pid=${oldpid:-?})" >>"$LOG"
  rm -rf "$LOCK"
  mkdir "$LOCK" && echo $$ >"$LOCK/pid"
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

# perl alarm 实现超时（macOS 无 GNU timeout；alarm 在 exec 后仍生效）
perl -e 'alarm shift @ARGV; exec @ARGV or die "exec failed: $!"' \
  "$TIMEOUT" claude -p "$PROMPT" --dangerously-skip-permissions >>"$LOG" 2>&1
RC=$?

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
