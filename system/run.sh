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

echo "=== RSI $MODE 场 $(date '+%F %T') ===" >>"$LOG"

if [ "$MODE" = "smoke" ]; then
  PROMPT="这是 RSI 系统链路冒烟测试。只回复两个字：正常。不要执行任何其他操作。"
else
  PROMPT="$(cat "$ROOT/system/prompts/$MODE.md")"
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
