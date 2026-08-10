#!/usr/bin/env python3
"""飞书收信：把人发给机器人的新消息自动写入 human/INBOX.md 未处理段。

每场会话启动前由 run.sh 调用。首次运行只建立检查点（不回灌历史消息）。
去重靠 message_id 集合，时间仅作辅助（飞书 create_time 只有分钟粒度）。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "human" / "INBOX.md"
CHECKPOINT = ROOT / "system" / ".inbox_checkpoint.json"
USER_OPEN_ID = "ou_6cc25a9ef6be867e0b986d1051f0bbaf"


def fetch_messages():
    p = subprocess.run(
        ["lark-cli", "im", "+chat-messages-list", "--as", "bot",
         "--user-id", USER_OPEN_ID, "--page-size", "50", "--sort", "desc"],
        capture_output=True, text=True, timeout=30,
    )
    data = json.loads(p.stdout)
    if not data.get("ok"):
        raise RuntimeError(f"lark-cli 返回异常: {p.stdout[:200]}")
    return data["data"]["messages"]


def user_messages(messages):
    """按时间正序返回人发出的文本消息 [(message_id, create_time, text)]。"""
    out = []
    for m in messages:
        if m.get("deleted") or m.get("sender", {}).get("sender_type") != "user":
            continue
        if m.get("msg_type") not in ("text", "post"):
            continue
        text = " ／ ".join(
            line.strip() for line in str(m.get("content", "")).splitlines() if line.strip()
        )
        if text:
            out.append((m["message_id"], m.get("create_time", ""), text))
    return list(reversed(out))


def main():
    msgs = user_messages(fetch_messages())

    if not CHECKPOINT.exists():
        CHECKPOINT.write_text(json.dumps(
            {"seen_ids": [mid for mid, _, _ in msgs]}, ensure_ascii=False))
        print(f"检查点已初始化（跳过历史消息 {len(msgs)} 条）")
        return

    seen = set(json.loads(CHECKPOINT.read_text()).get("seen_ids", []))
    fresh = [(mid, t, text) for mid, t, text in msgs if mid not in seen]
    if not fresh:
        print("无新消息")
        return

    inbox = INBOX.read_text(encoding="utf-8")
    anchor = "## 未处理\n"
    if anchor not in inbox:
        print("INBOX.md 缺少'## 未处理'段，放弃写入", file=sys.stderr)
        sys.exit(1)
    lines = "".join(f"- [ ] {text} ｜飞书 {t}\n" for _, t, text in fresh)
    inbox = inbox.replace(anchor, anchor + "\n" + lines, 1).replace("\n\n\n", "\n\n")
    INBOX.write_text(inbox, encoding="utf-8")

    seen.update(mid for mid, _, _ in fresh)
    CHECKPOINT.write_text(json.dumps(
        {"seen_ids": list(seen)[-300:]}, ensure_ascii=False))
    print(f"已收取 {len(fresh)} 条新指令进 INBOX")


if __name__ == "__main__":
    main()
