#!/usr/bin/env python3
"""飞书实时收信：WebSocket 长连接监听用户消息，即时写入 INBOX 并回执确认。

由 launchd（cn.jerryai.rsi-inbox-listener，KeepAlive）常驻运行。
与 pull_inbox.py 共享 .inbox_checkpoint.json 去重（拉取作为兜底保留）。
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "human" / "INBOX.md"
CHECKPOINT = ROOT / "system" / ".inbox_checkpoint.json"
USER_OPEN_ID = "ou_6cc25a9ef6be867e0b986d1051f0bbaf"
PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"


def log(msg):
    print(f"[{datetime.now():%F %T}] {msg}", file=sys.stderr, flush=True)


def load_seen():
    try:
        return set(json.loads(CHECKPOINT.read_text()).get("seen_ids", []))
    except Exception:
        return set()


def save_seen(seen):
    CHECKPOINT.write_text(json.dumps(
        {"seen_ids": list(seen)[-300:]}, ensure_ascii=False))


def append_inbox(text, ts):
    inbox = INBOX.read_text(encoding="utf-8")
    anchor = "## 未处理\n"
    if anchor not in inbox:
        log("INBOX.md 缺少'## 未处理'段，放弃写入")
        return False
    line = f"- [ ] {text} ｜飞书 {ts}\n"
    inbox = inbox.replace(anchor, anchor + "\n" + line, 1).replace("\n\n\n", "\n\n")
    INBOX.write_text(inbox, encoding="utf-8")
    return True


def ack(message_id):
    try:
        subprocess.run(
            ["lark-cli", "im", "+messages-reply", "--message-id", message_id,
             "--text", "✅ 已收进 INBOX，下一场会话（早 07:30 / 晚 21:30）执行。"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        log(f"回执失败（不影响收信）: {e}")


def handle(line):
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        return
    if ev.get("type") != "im.message.receive_v1":
        return
    if ev.get("sender_id") != USER_OPEN_ID:
        return
    mid = ev.get("message_id", "")
    text = " ／ ".join(
        l.strip() for l in str(ev.get("content", "")).splitlines() if l.strip())
    if not mid or not text:
        return
    seen = load_seen()
    if mid in seen:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if append_inbox(text, ts):
        seen.add(mid)
        save_seen(seen)
        log(f"已收信: {text[:50]}")
        ack(mid)


def main():
    os.environ["PATH"] = PATH + ":" + os.environ.get("PATH", "")
    log("启动飞书事件长连接")
    proc = subprocess.Popen(
        ["lark-cli", "event", "+subscribe",
         "--event-types", "im.message.receive_v1", "--compact", "--quiet"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    for line in proc.stdout:
        handle(line.strip())
    rc = proc.wait()
    log(f"长连接进程退出 rc={rc}，交由 launchd 重启")
    sys.exit(rc or 1)


if __name__ == "__main__":
    main()
