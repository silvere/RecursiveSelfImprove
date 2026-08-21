#!/usr/bin/env python3
"""cover_check.py — 题图去重判定（T-021 / W-006）

**它要防的事**：2026-08-13~08-16 连续四篇共用同一张库存封面，系统三天无感——
因为当时唯一在看的字段是 `uploaded_image_count`，它只回答"上传了几张"，
不回答"是不是同一张"。正常态取 1，异常态**也**取 1（见 STRATEGY 策略 10）。

**指纹用什么**：git blob sha。内容相同 → sha 相同，零依赖、零额外计算，
git 早就为每个文件算好了（线索见 LEDGER 2026-08-17 产出记录行）。

**封面是哪张**：复刻 `AIWriter/aiwriter/wechat.py::_pick_cover` 的口径——
优先 `cover.{png,jpg,jpeg,gif}`，否则取 `images/` 里按名字排序的第一张光栅图。
口径必须和真正上传封面的那段代码一致，否则查的是另一张图。

用法：
  cover_check.py --dir posts/2026-08-21/representation-cost   # 判单篇（与最近 N 篇比）
  cover_check.py --audit                                      # 对全部存量回跑，列出所有重复
退出码：0 通过 ｜ 1 命中重复 ｜ 2 用法/环境错
"""
import argparse
import subprocess
import sys
from collections import defaultdict

AIWRITER = "/Users/jingweisun/Code/AIWriter"
COVER_NAMES = ["cover.png", "cover.jpg", "cover.jpeg", "cover.gif"]
RASTER = (".png", ".jpg", ".jpeg", ".gif")
WINDOW = 7  # 与最近 7 篇比对


def git(*args, cwd=AIWRITER):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"::error::git {' '.join(args)} 失败：{r.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return r.stdout


def tree(ref):
    """{post_dir: {文件名: blob_sha}}，只收 posts/<date>/<slug>/ 下的文件。"""
    out = defaultdict(dict)
    for line in git("ls-tree", "-r", ref, "--", "posts/").splitlines():
        meta, path = line.split("\t", 1)
        sha = meta.split()[2]
        parts = path.split("/")
        if len(parts) < 4:
            continue
        post = "/".join(parts[:3])
        out[post]["/".join(parts[3:])] = sha
    return out


def cover_of(files):
    """复刻 _pick_cover：cover.* 优先，否则正文第一张光栅图。返回 (相对路径, sha) 或 None。"""
    for name in COVER_NAMES:
        if name in files:
            return name, files[name]
    imgs = sorted(f for f in files if f.lower().endswith(RASTER))
    return (imgs[0], files[imgs[0]]) if imgs else None


def fetch_ref(ref: str) -> None:
    """判定前把 ref 拉新。

    2026-08-22 s2 实测到的真 bug：本判定读的是**本地**的 origin/main ref，而配图 CI 刚
    把题图推上去时本地 ref 还停在 ship 之前的 commit——于是"图明明在远端"被报成
    "✗ 没有任何题图"，RC=4 拒绝同步。两种完全不同的情况（真没图 / 我的数据过期了）
    共用了同一个结论，正是 STRATEGY 策略 11 说的：机检信号再强，输入陈旧一样得出假结论。
    """
    if not ref.startswith("origin/"):
        return
    branch = ref.split("/", 1)[1]
    r = subprocess.run(["git", "fetch", "origin", branch, "-q"], cwd=AIWRITER,
                       capture_output=True, text=True)
    if r.returncode != 0:
        # 离线时不阻断判定，但必须显式告诉调用者"下面这个结论基于可能过期的数据"
        print(f"::warning::git fetch origin {branch} 失败（{r.stderr.strip()[:80]}），"
              f"以下判定基于本地可能过期的 {ref}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="要判定的 post 目录，如 posts/2026-08-21/xxx")
    ap.add_argument("--audit", action="store_true", help="对全部存量回跑")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--no-fetch", action="store_true",
                    help="跳过判定前的 git fetch（仅用于测试陈旧 ref 的行为）")
    ap.add_argument("--window", type=int, default=WINDOW)
    a = ap.parse_args()
    if not a.dir and not a.audit:
        print(__doc__)
        return 2

    if not a.no_fetch:
        fetch_ref(a.ref)
    t = tree(a.ref)
    posts = sorted(t)  # posts/<date>/<slug> —— 日期在前，字典序即时间序

    if a.audit:
        seen, dups, covered = {}, [], 0
        for p in posts:
            c = cover_of(t[p])
            if not c:
                continue
            covered += 1
            name, sha = c
            if sha in seen:
                dups.append((p, name, sha[:12], seen[sha]))
            else:
                seen[sha] = p
        for p, name, sha, first in dups:
            print(f"✗ {p}/{name} 与 {first} 同图（blob {sha}）")
        print(f"回跑：{covered} 篇有题图，{len(set(x[3] for x in dups))} 组重复、"
              f"共 {len(dups)} 篇撞图，{covered - len(dups)} 篇唯一")
        return 1 if dups else 0

    target = a.dir.rstrip("/")
    if target not in t:
        print(f"::error::{a.ref} 上没有 {target}")
        return 2
    c = cover_of(t[target])
    if not c:
        print(f"✗ {target} 在 {a.ref} 上没有任何题图——封面缺失本身就该拒（微信同步会失败）。"
              f"若配图 CI 刚成功，先确认 fetch 是否失败（见上方 warning）")
        return 1
    name, sha = c
    idx = posts.index(target)
    recent = posts[max(0, idx - a.window):idx]
    for p in recent:
        pc = cover_of(t[p])
        if pc and pc[1] == sha:
            print(f"✗ 题图与 {p}/{pc[0]} 是同一张（blob {sha[:12]}）——最近 {a.window} 篇内重复，拒")
            return 1
    print(f"✓ 题图 {name} (blob {sha[:12]}) 与最近 {len(recent)} 篇均不重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
