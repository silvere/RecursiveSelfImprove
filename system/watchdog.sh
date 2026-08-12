#!/bin/bash
# RSI 看门狗：检测系统停摆并告警。独立于会话调度，会话按协议禁令无法卸载它。
# 触发条件：①超过 26 小时无新 journal ②调度任务从 launchctl 消失
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ALARM=""

newest="$(ls -t "$ROOT"/journal/20*.md 2>/dev/null | head -1)"
if [ -z "$newest" ]; then
  ALARM="journal 目录为空"
else
  age_h=$(( ( $(date +%s) - $(stat -f %m "$newest") ) / 3600 ))
  if [ "$age_h" -ge 26 ]; then
    ALARM="已 ${age_h} 小时无新 journal（最近：$(basename "$newest")）"
  fi
fi

for job in cn.jerryai.rsi-work cn.jerryai.rsi-pm; do
  if ! launchctl list | grep -q "$job"; then
    ALARM="${ALARM:+$ALARM；}调度任务 $job 不在 launchctl 列表中"
  fi
done

if [ -n "$ALARM" ]; then
  "$ROOT/system/notify.sh" "🚨 **RSI 看门狗告警**：$ALARM
系统可能停摆。请检查 \`launchctl list | grep rsi\` 与 system/logs/ 最新日志（参考 L-008 事故处置）。"
fi
exit 0
