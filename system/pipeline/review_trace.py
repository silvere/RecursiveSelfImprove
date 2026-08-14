#!/usr/bin/env python3
"""审稿痕迹检查器（T-015）——让 GOAL 验收第 2 条"可溯源"可机器判定。

规范见 docs/review-trace-spec.md。一句话：LEDGER 产出记录行的「审稿记录」字段
填**文章目录**，目录里必须同时存在三件可回溯的证据（选题依据／论点竞技场结论／
七刀审稿记录），任一缺失即该篇不可溯源。

作为库用：
    from review_trace import check_article
    ok, missing = check_article(Path(".../articles/2026-08-08-hobby"))

作为命令用：
    python3 system/pipeline/review_trace.py <文章目录> [<文章目录>...]
    python3 system/pipeline/review_trace.py --ledger        # 检查 LEDGER 里记的每一篇
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# 三件套：字段名 → (候选文件名, 该文件里必须出现的最小内容特征)
REQUIRED = {
    "选题依据": (("01-brief.md", "00-topic.md"), r"talk_id|source_url|选题|来源"),
    "论点竞技场结论": (("03-arena.md", "02-arena.md"), r".{200,}"),
    "七刀审稿记录": (("06-review.md", "05-review.md"), r"必修|驳回|刀"),
}

MIN_BYTES = 200  # 低于此视为占位空文件——空文件与"没写"不能共用一个通过结果


def check_article(d: Path) -> tuple[bool, list[str]]:
    """返回 (是否可溯源, 缺失项说明列表)。"""
    if not d.is_dir():
        return False, [f"目录不存在：{d}"]

    missing = []
    for label, (names, pattern) in REQUIRED.items():
        hit = None
        for n in names:
            p = d / n
            if p.is_file() and p.stat().st_size >= MIN_BYTES:
                text = p.read_text(encoding="utf-8", errors="replace")
                if re.search(pattern, text, re.S):
                    hit = n
                    break
        if not hit:
            missing.append(f"{label}（需 {' 或 '.join(names)}，非空且含实质内容）")

    if not (d / "final.md").is_file():
        missing.append("终稿 final.md")
    return not missing, missing


def ledger_article_dirs(ledger_text: str) -> list[tuple[str, str]]:
    """从 LEDGER 文章产出记录段抽 (日期, 审稿记录字段) 对。"""
    m = re.search(r"^##\s*文章产出记录\s*$(.*?)(?=^##\s|\Z)", ledger_text, re.M | re.S)
    out = []
    for line in (m.group(1) if m else "").splitlines():
        parts = [p.strip() for p in line.strip().split("｜")]
        if len(parts) >= 5 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[0]):
            out.append((parts[0], parts[3]))
    return out


def resolve(field: str) -> Path | None:
    """从「审稿记录」字段里抽出一个可检查的文章目录路径；抽不出返回 None。"""
    m = re.search(r"([~/][^\s｜（(]*articles/[0-9A-Za-z._-]+)", field)
    if not m:
        return None
    p = Path(m.group(1)).expanduser()
    return p.parent if p.is_file() or p.suffix == ".md" else p


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--ledger":
        ledger = (REPO / "LEDGER.md").read_text(encoding="utf-8", errors="replace")
        rows = ledger_article_dirs(ledger)
        if not rows:
            print("[错误] LEDGER「文章产出记录」段没有可解析的原始行", file=sys.stderr)
            return 2
        bad = 0
        for day, field in rows:
            d = resolve(field)
            if d is None:
                print(f"✗ {day} 审稿记录字段里没有文章目录路径：{field[:60]}…")
                bad += 1
                continue
            ok, missing = check_article(d)
            print(f'{"✓" if ok else "✗"} {day} {d}' + ("" if ok else f'  缺：{"；".join(missing)}'))
            bad += 0 if ok else 1
        print(f"\n可溯源 {len(rows) - bad}/{len(rows)} 篇")
        return 0 if bad == 0 else 1

    if not argv:
        print(__doc__)
        return 2
    bad = 0
    for a in argv:
        ok, missing = check_article(Path(a).expanduser())
        print(f'{"✓" if ok else "✗"} {a}' + ("" if ok else f'  缺：{"；".join(missing)}'))
        bad += 0 if ok else 1
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
