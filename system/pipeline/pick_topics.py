#!/usr/bin/env python3
"""从 wtqn 问题库取当日选题候选，产出 workspace/topics/YYYY-MM-DD.md。

分工（刻意的）：脚本只做机械部分——定位库、解析 frontmatter、排除已用过的题、
按 importance 排序、把可回溯字段抄全。**选哪一条写、写什么角度，由会话判断**，
脚本不假装能评判内容质量，只保证会话每天不必重新查库路径、不会重复选题。

用法：
    python3 system/pipeline/pick_topics.py                 # 产出今天的候选
    python3 system/pipeline/pick_topics.py --date 2026-08-15
    python3 system/pipeline/pick_topics.py --force         # 覆盖已存在的候选文件

失败即非零退出并明确报错（库不存在 / 可用条目为 0），不产出空文件——
空文件与"没有产出"共用一个静默返回值正是 L-010 那类"看起来正常"的故障。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
TOPICS_DIR = REPO / "workspace" / "topics"

# 问题库真实位置（不是 ~/Code/wtqn/data，该目录不存在——2026-08-14 s2 查实）
DEFAULT_BANK = Path(
    "/Users/jingweisun/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "Silvere/AI-Articles/Question-Bank"
)

MIN_IMPORTANCE = 7
N_MAIN = 3        # 主候选数（GOAL 验收要求每天 3 条可回溯候选）
N_BACKUP = 8      # 备选池：importance 高分里技术/科学类偏多，会话常需从池里换，故留宽


def load_entries(bank: Path) -> list[dict]:
    """解析 sources/**/*.md 的 frontmatter，返回带回溯字段的条目列表。"""
    src = bank / "sources"
    if not src.is_dir():
        sys.exit(f"[错误] 问题库 sources 目录不存在：{src}")

    entries = []
    for path in sorted(src.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict) or not fm.get("core_question"):
            continue

        entries.append(
            {
                "path": path,
                "question": str(fm["core_question"]).strip(),
                "talk_id": str(fm.get("talk_id", "")),
                "question_idx": fm.get("question_idx", ""),
                "importance": int(fm.get("importance") or 0),
                "source_url": str(fm.get("source_url", "")),
                "speaker": str(fm.get("speaker", "")),
                "title": str(fm.get("title", "")),
                "date_captured": str(fm.get("date_captured", "")),
                "tags": fm.get("tags") or [],
                "evidence": extract_evidence(text),
            }
        )
    return entries


def extract_evidence(text: str) -> str:
    """取 `## Evidence from Talk` 段的第一段原文引语，作为成稿时的一手素材。"""
    m = re.search(r"##\s*Evidence from Talk\s*\n(.+?)(?=\n##\s|\Z)", text, re.S)
    if not m:
        return ""
    body = [ln.strip() for ln in m.group(1).strip().splitlines() if ln.strip()]
    return body[0][:300] if body else ""


def used_keys() -> set[str]:
    """已在往期候选文件里出现过的题，不再重复推荐。

    键取 `talk_id#question_idx`：同一场演讲的不同问题算不同题，同一问题不重复。
    """
    used: set[str] = set()
    if not TOPICS_DIR.is_dir():
        return used
    for f in TOPICS_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="replace")
        for tid, idx in re.findall(r"talk_id[：:\s`]*([0-9a-f]{6,})\D{0,40}?question_idx[：:\s`]*(\d+)", text):
            used.add(f"{tid}#{idx}")
        # 兜底：只写了 talk_id 没写 idx 的旧格式，整场演讲一并排除
        for tid in re.findall(r"talk_id[：:\s`]*([0-9a-f]{6,})", text):
            used.add(f"{tid}#*")
    return used


def pick(entries: list[dict], used: set[str], n: int) -> list[dict]:
    """按 importance 降序取 n 条，同一 talk_id 当天只出一条（避免三条同源）。"""
    # 两趟稳定排序：先入库日期新的在前，再按 importance 降序（同分保留"新的优先"）
    ranked = sorted(entries, key=lambda e: (e["date_captured"], str(e["path"])), reverse=True)
    ranked = sorted(ranked, key=lambda e: -e["importance"])
    out, seen_talks = [], set()
    for e in ranked:
        if e["importance"] < MIN_IMPORTANCE:
            continue
        key = f'{e["talk_id"]}#{e["question_idx"]}'
        if key in used or f'{e["talk_id"]}#*' in used:
            continue
        if e["talk_id"] in seen_talks:
            continue
        seen_talks.add(e["talk_id"])
        out.append(e)
        if len(out) >= n:
            break
    return out


def render_entry(e: dict, bank: Path) -> str:
    rel = e["path"].relative_to(bank)
    lines = [
        f'**问题**：{e["question"]}',
        "",
        "**可回溯**",
        f'- 条目：`Question-Bank/{rel}`',
        f'- talk_id：`{e["talk_id"]}` ｜ question_idx：`{e["question_idx"]}` ｜ '
        f'importance：{e["importance"]} ｜ 入库：{e["date_captured"]}',
        f'- 演讲人：{e["speaker"]}',
        f'- 原始链接：{e["source_url"]}',
    ]
    if e["evidence"]:
        lines += ["", f'**演讲原句**：{e["evidence"]}']
    lines += ["", "**为什么值得写 / 论点角度**：_（待会话补写——脚本不做内容判断）_"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    ap.add_argument("--force", action="store_true", help="覆盖已存在的候选文件")
    args = ap.parse_args()

    if not args.bank.is_dir():
        sys.exit(f"[错误] 问题库不存在：{args.bank}")

    out_path = TOPICS_DIR / f"{args.date}.md"
    if out_path.exists() and not args.force:
        sys.exit(f"[跳过] {out_path} 已存在（会话可能已补写角度判断）。要重生成加 --force")

    entries = load_entries(args.bank)
    if not entries:
        sys.exit(f"[错误] 库里解析到 0 条带 core_question 的条目：{args.bank}")

    used = used_keys()
    picked = pick(entries, used, N_MAIN + N_BACKUP)
    if len(picked) < N_MAIN:
        sys.exit(
            f"[错误] 可用候选只有 {len(picked)} 条（要求 ≥{N_MAIN}）："
            f"库 {len(entries)} 条，已用 {len(used)} 键，importance 阈值 {MIN_IMPORTANCE}。"
            "库该补货了"
        )

    main_list, backup = picked[:N_MAIN], picked[N_MAIN:]
    doc = [
        "---",
        f"title: 选题候选 {args.date}",
        f"date: {args.date}",
        "draft: true",
        "tags:\n  - 选题\n  - wtqn\n  - T-012",
        f"summary: 由 system/pipeline/pick_topics.py 从 wtqn 问题库自动筛出的 {N_MAIN} 条候选"
        f"（库 {len(entries)} 条，已排除往期用过的 {len(used)} 个键），每条带 talk_id/question_idx/"
        "原始链接可回溯；论点角度由会话补写。",
        "---",
        "",
        f"# 选题候选 · {args.date}",
        "",
        f"库：`{args.bank}`｜可解析条目 {len(entries)} 条｜importance ≥ {MIN_IMPORTANCE}"
        f"｜已排除往期用过 {len(used)} 个键｜生成：`system/pipeline/pick_topics.py`",
        "",
    ]
    for i, e in enumerate(main_list, 1):
        doc += [f"## 候选 {i}", "", render_entry(e, args.bank), "", "---", ""]
    if backup:
        doc += ["## 备选池（主候选都不顺手时替换）", ""]
        for e in backup:
            doc.append(
                f'- {e["question"][:60]}…（`{e["talk_id"]}#{e["question_idx"]}`，'
                f'importance {e["importance"]}）'
            )
        doc.append("")

    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(doc), encoding="utf-8")
    print(f"✓ {out_path}（主候选 {len(main_list)} + 备选 {len(backup)}，库 {len(entries)} 条，已排除 {len(used)} 键）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
