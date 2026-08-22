#!/usr/bin/env python3
"""evidence_grade.py — 结论句的证据分级机检（落地 STRATEGY 策略 11 / L-047）

**它要防的事**：策略 11 规定"任何'完成/通过/达标'类结论必须至少有一条 L1–L3 级证据，
L4（会话自评）不得单独成立"。但这条纪律落成的当天，它自己的执行方式是
"下一场会话拿眼睛扫一遍最近 10 条条目"——**又是一个靠记性的验收动作**，
正是 L-046 当场判死的形态（"验收动作必须比被验收的纪律更不依赖记性"）。
本脚本把"这条结论算不算数"从判断题换成识别题：有没有 L1–L3 级证据标记，机器说了算。

**四级信号（STRATEGY 策略 11）**：
  L1 机检     退出码/RC、脚本文件名、grep/git 等命令、blob sha、仓库内文件路径
  L2 外部回执 CI run 号、media_id、message_id、commit hash、HTTP 状态码
  L3 跨场复核 明写"复核/跨场复核 → 相符/不符"
  L4 会话自评 以上三者一个都没有 → **裸奔**

**刻意的边界**：本脚本只判"有没有可核验的证据锚点"，不判"这条证据对不对"
（对不对是策略 7 的跨场复核该干的事，那需要真的复跑命令）。
所以它的假阳性是"引用了一个错的 commit hash 也算 L2"——这是有意的：
锚点存在，下一场就**可以**去复跑；锚点不存在，结构上无从复核。

用法：
  evidence_grade.py                       # 扫 LEDGER 条目段全量，打印分级统计
  evidence_grade.py --list-bare           # 只列 L4 裸奔条目
  evidence_grade.py --gate --since L-048  # 门禁模式：只看编号 > 基线的新条目，有裸奔即非零退出
  evidence_grade.py --file X --section Y  # 换文件/换段落
退出码：0 无裸奔（或非门禁模式正常打印）｜ 1 门禁模式下发现裸奔 ｜ 2 用法/环境错
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 结论词：出现其一才要求证据。刻意不含"记录/登记/发现"这类陈述性动词——
# 策略 11 管的是"完成/通过/达标"类断言，不是所有句子。
CLAIM_WORDS = [
    "完成", "通过", "达成", "达标", "闭环", "验收", "成功",
    "已落地", "生效", "修好", "修复", "跑通", "解决",
]

# 证据锚点。每条都必须是"下一场会话能拿去复跑或点开"的东西。
EVIDENCE = {
    "L1": [
        (r"RC\s*=\s*\d", "退出码"),
        (r"退出码\s*\d", "退出码"),
        (r"\b(grep|awk|sed|git|python3|bash|ls|wc|curl)\s+-?[-\w]", "命令"),
        (r"blob\s*(sha)?\s*=?\s*[0-9a-f]{6,}", "blob sha"),
        # 任何带已知扩展名的文件名/路径 —— 判据是"下一场能不能点开它"，
        # 不是"它在不在本仓"（L-034 的锚点是 ~/Code/AIWriter2/skills/aiwriter2.md，
        # L-045 的是 dashboard/index.html，第一版正则把这两条全判成裸奔，假阳性 3/4）
        (r"(?:[\w~.-]+/)*[\w.-]+\.(?:py|sh|md|json|html|csv|log|ya?ml|txt|jpe?g|png)\b", "文件锚点"),
    ],
    "L2": [
        (r"\brun\s*#?\s*\d{7,}", "CI run 号"),
        (r"media_id\s*=", "media_id"),
        (r"message_id\s*=", "message_id"),
        (r"commit[=\s]*`?[0-9a-f]{7,}", "commit hash"),
        (r"\berrcode\s*=?\s*\d+", "接口返回码"),
        (r"HTTP\s*\d{3}", "HTTP 状态码"),
    ],
    "L3": [
        (r"复核.{0,20}(相符|不符)", "跨场复核结论"),
        (r"(上场|上一场)证据复核", "跨场复核"),
    ],
}


def read_section(path, section):
    """取 `## <section>` 到下一个 `## ` 之间的正文。"""
    if not os.path.exists(path):
        print(f"::error::找不到文件 {path}", file=sys.stderr)
        sys.exit(2)
    lines = open(path, encoding="utf-8").read().splitlines()
    out, inside = [], False
    for ln in lines:
        if ln.startswith("## "):
            inside = ln[3:].strip() == section
            continue
        if inside:
            out.append(ln)
    if not out:
        print(f"::error::{path} 里没有 `## {section}` 段或该段为空", file=sys.stderr)
        sys.exit(2)
    return out


def split_entries(lines):
    """按 `[L-NNN]` / `[W-NNN]` 行首切条目，返回 [(编号, 全文)]。"""
    entries, cur_id, buf = [], None, []
    for ln in lines:
        m = re.match(r"^\[([LW]-\d+)\]", ln)
        if m:
            if cur_id:
                entries.append((cur_id, "\n".join(buf)))
            cur_id, buf = m.group(1), [ln]
        elif cur_id:
            buf.append(ln)
    if cur_id:
        entries.append((cur_id, "\n".join(buf)))
    return entries


def grade(text):
    """返回 (最高级别, {级别: [命中的锚点名]})。无结论词返回 (None, {})。"""
    if not any(w in text for w in CLAIM_WORDS):
        return None, {}
    hits = {}
    for level in ("L1", "L2", "L3"):
        for pat, name in EVIDENCE[level]:
            if re.search(pat, text):
                hits.setdefault(level, [])
                if name not in hits[level]:
                    hits[level].append(name)
    best = next((lv for lv in ("L1", "L2", "L3") if lv in hits), "L4")
    return best, hits


def head_max_id(path, section):
    """HEAD 版本里该段的最大条目编号，形如 "L-048"。取不到返回 None（＝全量检查）。"""
    rel = os.path.relpath(os.path.abspath(path), ROOT)
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    ids = [int(m.group(2)) for m in
           (re.match(r"^\[([LW])-(\d+)\]", ln) for ln in r.stdout.splitlines()) if m]
    return f"L-{max(ids):03d}" if ids else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.path.join(ROOT, "LEDGER.md"))
    ap.add_argument("--section", default="条目")
    ap.add_argument("--list-bare", action="store_true")
    ap.add_argument("--gate", action="store_true", help="发现裸奔即非零退出")
    ap.add_argument("--since", default=None, help="只检查编号严格大于该基线的条目，如 L-048")
    ap.add_argument("--new", action="store_true",
                    help="基线自动取 HEAD 版本同文件的最大编号——即只检查本次 commit 新增的条目")
    a = ap.parse_args()

    if a.new:
        if a.since:
            print("::error::--new 与 --since 互斥", file=sys.stderr)
            sys.exit(2)
        a.since = head_max_id(a.file, a.section)

    entries = split_entries(read_section(a.file, a.section))
    if not entries:
        print(f"::error::`## {a.section}` 段里没有 [L-NNN] 形式的条目", file=sys.stderr)
        sys.exit(2)

    floor = -1
    if a.since:
        m = re.match(r"^[LW]-(\d+)$", a.since)
        if not m:
            print(f"::error::--since 需形如 L-048，收到 {a.since}", file=sys.stderr)
            sys.exit(2)
        floor = int(m.group(1))

    tally = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "无结论句": 0}
    bare, checked = [], 0
    for eid, text in entries:
        if int(eid.split("-")[1]) <= floor:
            continue
        checked += 1
        best, hits = grade(text)
        if best is None:
            tally["无结论句"] += 1
            continue
        tally[best] += 1
        if best == "L4":
            bare.append(eid)
        if a.list_bare and best == "L4":
            head = text.splitlines()[0][:90]
            print(f"  {eid}  {head}")

    scope = f"（基线 {a.since} 之后）" if a.since else "（全量）"
    print(f"{os.path.basename(a.file)} `## {a.section}` 段{scope}：检查 {checked} 条")
    print("  " + " ｜ ".join(f"{k} {v}" for k, v in tally.items()))
    if bare:
        print(f"  L4 裸奔：{', '.join(bare)}")

    if a.gate and bare:
        print(f"::error::{len(bare)} 条结论句拿不出 L1–L3 级证据（策略 11）：{', '.join(bare)}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
