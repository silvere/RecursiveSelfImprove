#!/bin/bash
# RSI 飞书通知：notify.sh "<markdown 消息>"。失败不中断调用方。
# 断网时飞书这条路整条不通——2026-08-19~20 本机断外网两天，8 场会话全挂，8 条告警一条都没送到，
# 人两天里完全不知道系统停了（见 LEDGER L-038）。所以：发失败就落盘排队 + 走 macOS 本地通知
# （不需要网），下一次发成功时把积压的一并补发，网一恢复人就能补看到断网期间发生过什么。
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUEUE="$ROOT/system/state/undelivered-alerts.md"
MSG="${1:-RSI 通知（空消息）}"

send() {
  lark-cli im +messages-send \
    --user-id ou_6cc25a9ef6be867e0b986d1051f0bbaf \
    --markdown "$1"
}

if send "$MSG"; then
  if [ -s "$QUEUE" ]; then
    if send "📮 **补发断网期间积压的 $(grep -c '^## ' "$QUEUE") 条告警**（发生时本机发不出去）

$(cat "$QUEUE")"; then
      : >"$QUEUE"
    fi
  fi
  exit 0
fi

# 走到这里 = 网络/凭证不通。落盘的队列是唯一还能留住这条告警的地方。
mkdir -p "$(dirname "$QUEUE")"
printf '## %s\n\n%s\n\n' "$(date '+%F %T')" "$MSG" >>"$QUEUE"
osascript -e "display notification \"RSI 有告警发不出去，已落盘排队\" with title \"RSI $(date '+%H:%M') 断网\"" 2>/dev/null || true
exit 1
