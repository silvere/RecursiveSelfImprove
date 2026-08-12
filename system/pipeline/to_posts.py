#!/usr/bin/env python3
"""
to_posts.py — 转换桥：AIWriter2 产物 → AIWriter/posts 结构（wechat-sync 可识别）

背景（L-006）：aiwriter2 的成稿在 AIWriter2/articles/<slug>/final.md（带 YAML frontmatter 的纯 markdown），
而 wechat-sync 的 sync_drafts.py 只认 AIWriter/posts/YYYY-MM-DD/<slug>/article.html，
且 aiwriter/wechat.py::_pick_cover 要求目录里有 cover.* 或正文第一张光栅图，否则同步报错。

本脚本做三件事：
  1. 剥离 frontmatter，取 title/summary/date；正文原样保留
  2. 在正文首段之后插入一个 concept 图占位符——CI「自动填充文章配图」(fill_images.py) 会把它
     替换成 images/concept_01.png，从而给 _pick_cover 提供封面来源（本链路不需要单独生成 cover.jpg）
  3. 调用 AIWriter/skills/scripts/md_to_html.py 套用官方模板生成 article.html

用法：
  python3 system/pipeline/to_posts.py <aiwriter2_article_dir> [--date YYYY-MM-DD] [--slug xxx] [--category 分类]
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

AIWRITER = Path("/Users/jingweisun/Code/AIWriter")
MD_TO_HTML = AIWRITER / "skills/scripts/md_to_html.py"

# 占位符必须匹配 fill_images.py 的 _PLACEHOLDER_RE：
#   <div class="img-placeholder (concept|diagram|understanding)"[^>]*>(.*?</details>)\s*(?:</div>)?
PLACEHOLDER = """<div class="img-placeholder concept">
  <div class="img-placeholder-icon">🖼️</div>
  <div class="img-placeholder-label">概念图</div>
  <details><summary>提示词</summary><pre>{prompt}</pre></details>
</div>"""


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """返回 (frontmatter dict, 去掉 frontmatter 的正文)。只解析扁平的 key: value。"""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():]


def build_md(body: str, meta: dict, pub_date: str, category: str, img_prompt: str) -> str:
    """组装 article.md：一级标题 + 发布日期行 + 正文（首段后插图占位符）。"""
    body = body.lstrip("\n")
    title_m = re.match(r"^# (.+)\n", body)
    title = title_m.group(1).strip() if title_m else meta.get("title", "无标题")
    if title_m:
        body = body[title_m.end():].lstrip("\n")

    paras = body.split("\n\n")
    placeholder = PLACEHOLDER.format(prompt=img_prompt)
    # 插在首段之后：既是正文配图，也是 _pick_cover 的封面来源
    paras.insert(1, placeholder)
    body = "\n\n".join(paras)

    return f"# {title}\n\n> **发布日期**：{pub_date} | **分类**：{category}\n\n{body}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir", help="AIWriter2 文章目录（含 final.md）")
    ap.add_argument("--date", default=str(date.today()))
    ap.add_argument("--slug", default="")
    ap.add_argument("--category", default="认知深度")
    ap.add_argument("--img-prompt", default="flat minimalist illustration, person lying in bed at night "
                                            "scrolling phone, soft blue light, no text, clean background")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.src_dir)
    final = src / "final.md"
    if not final.exists():
        print(f"::error::{final} 不存在", file=sys.stderr)
        return 1

    meta, body = parse_frontmatter(final.read_text(encoding="utf-8"))
    slug = args.slug or src.name
    out_dir = AIWRITER / "posts" / args.date / slug
    md_path = out_dir / "article.md"

    article_md = build_md(body, meta, args.date, args.category, args.img_prompt)
    if args.dry_run:
        print(article_md[:600])
        print(f"...\n[dry-run] 将写入 {md_path}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text(article_md, encoding="utf-8")
    print(f"✓ {md_path} ({len(article_md)} 字符)")

    cmd = [
        sys.executable, str(MD_TO_HTML), str(md_path),
        "--category", args.category,
        "--date", args.date,
        "--lead", meta.get("summary", ""),
        "--out", str(out_dir / "article.html"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"::error::md_to_html 失败：{r.stderr}", file=sys.stderr)
        return 1
    print(r.stdout.strip())
    print(f"✓ {out_dir / 'article.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
