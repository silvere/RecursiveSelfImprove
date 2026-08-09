#!/bin/bash
# RSI 飞书通知：notify.sh "<markdown 消息>"。失败不中断调用方。
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
MSG="${1:-RSI 通知（空消息）}"
lark-cli im +messages-send \
  --user-id ou_6cc25a9ef6be867e0b986d1051f0bbaf \
  --markdown "$MSG"
