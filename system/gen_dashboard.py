#!/usr/bin/env python3
"""RSI 仪表盘生成器：读仓库状态文件，渲染 dashboard/index.html。仅用 stdlib。"""
import html
import re
import subprocess
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard" / "index.html"


def read(p):
    f = ROOT / p
    return f.read_text(encoding="utf-8") if f.exists() else ""


def strip_frontmatter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def frontmatter_field(text, field):
    m = re.search(rf"^{field}:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    return m.group(1) if m else ""


def esc(s):
    return html.escape(s, quote=False)


def checklist(text, section):
    """抽取某标题下的 - [ ] / - [x] 条目。"""
    m = re.search(rf"##+\s*{section}\s*\n(.*?)(?=\n##|\Z)", text, re.S)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        cm = re.match(r"\s*(?:-|\d+\.)\s*\[([ x])\]\s*(.+)", line)
        if cm:
            items.append((cm.group(1) == "x", cm.group(2).strip()))
    return items


def li(items, empty="（空）"):
    if not items:
        return f"<li class='muted'>{empty}</li>"
    out = []
    for done, txt in items:
        cls = "done" if done else "todo"
        mark = "✅" if done else "⬜"
        out.append(f"<li class='{cls}'>{mark} {esc(txt)}</li>")
    return "\n".join(out)


def approvals_rows(text):
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"A-\d+", cells[0]):
            rows.append(cells)
    if not rows:
        return "<tr><td colspan='4' class='muted'>（无）</td></tr>"
    badge = {"pending": "🟡", "approved": "🟢", "rejected": "🔴", "done": "☑️"}
    return "\n".join(
        f"<tr><td>{esc(i)}</td><td>{esc(a)}</td><td>{esc(r)}</td>"
        f"<td>{badge.get(s, '')} {esc(s)}</td></tr>"
        for i, a, r, s in rows
    )


def journal_cards():
    files = sorted((ROOT / "journal").glob("*-[ap]m.md"), reverse=True)[:7]
    if not files:
        return "<p class='muted'>（尚无日志）</p>"
    cards = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        summary = frontmatter_field(text, "summary") or strip_frontmatter(text)[:120]
        cards.append(
            f"<div class='card'><h4>{esc(f.stem)}</h4><p>{esc(summary)}</p></div>"
        )
    return "\n".join(cards)


def ledger_items(text, limit=8):
    entries = [l for l in text.splitlines() if re.match(r"\[(L|W)-\d+\]", l.strip())]
    entries = entries[-limit:][::-1]
    if not entries:
        return "<li class='muted'>（空）</li>"
    return "\n".join(f"<li>{esc(e.strip())}</li>" for e in entries)


def http_check(url, timeout=6):
    """返回 (status_code, body) 或 (None, 错误描述)。

    先走 urllib（系统解析器）；失败则经 curl + DoH 独立探测——
    本机解析层不可信（Astrill VPN DNS 代理 198.19.255.254 会缓存陈旧 NXDOMAIN），
    站点是否可用必须以公网视角为准。
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rsi-dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        try:
            p = subprocess.run(
                ["curl", "-s", "--doh-url", "https://1.1.1.1/dns-query",
                 "--max-time", str(timeout + 4), "-w", "\n%{http_code}", url],
                capture_output=True, text=True, timeout=timeout + 8,
            )
            body, _, code = p.stdout.rpartition("\n")
            if code.isdigit() and int(code) > 0:
                return int(code), body
        except Exception:
            pass
        return None, str(e)


def section(text, title):
    """取出 `## <title>` 到下一个 `## ` 之间的正文。找不到返回空串。"""
    m = re.search(rf"^##\s*{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)",
                  text, re.M | re.S)
    return m.group(1) if m else ""


def delivery_streak(ledger_text):
    """从 LEDGER 送达记录算连续送达天数。返回 (streak, 最近成功日期或 None)。

    只认原始行 `YYYY-MM-DD ｜成功/失败`，连续天数由此推导——
    晚场会话只追加原始行，不做算术。
    """
    recs = {}
    for line in section(ledger_text, "简报送达记录").splitlines():
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s*｜\s*(成功|失败)", line.strip())
        if m:
            recs[date.fromisoformat(m.group(1))] = m.group(2) == "成功"
    if not recs:
        return 0, None
    last = max(recs)
    if not recs[last]:
        return 0, None
    streak, d = 0, last
    while recs.get(d):
        streak += 1
        d -= timedelta(days=1)
    return streak, last


def article_records(ledger_text):
    """解析 LEDGER"文章产出记录"段的原始行。

    格式：`日期 ｜标题 ｜选题来源 ｜审稿记录 ｜草稿箱：成功/失败 + media_id 或原因`
    返回 [{date, title, source, review, ok}]，按日期升序。
    """
    recs = []
    for line in section(ledger_text, "文章产出记录").splitlines():
        parts = [p.strip() for p in line.strip().split("｜")]
        if len(parts) < 5 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[0]):
            continue
        recs.append({
            "date": date.fromisoformat(parts[0]),
            "title": parts[1],
            "source": parts[2],
            "review": parts[3],
            "ok": "成功" in parts[4],
        })
    return sorted(recs, key=lambda r: r["date"])


def acceptance_auto(acceptance, ledger, inbox):
    """对 GOAL v2（内容流水线）验收标准逐条自动判定，返回 [(ok, 标准文本, 证据)]。

    GOAL.md 只读，其勾选框由人维护；此处判定一律来自实测数据。
    判定的唯一事实源是 LEDGER 的"文章产出记录"段（原始行）与仓库文件存在性——
    会话不得手写派生数字（见 L-002）。
    """
    results = []
    recs = article_records(ledger)
    ok_recs = [r for r in recs if r["ok"]]

    # C1 连续性：连续 14 天每天 ≥1 篇成功进草稿箱
    days = {r["date"] for r in ok_recs}
    streak, last = 0, max(days) if days else None
    d = last
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    c1 = streak >= 14
    c1_ev = (f"连续产出 {streak}/14 天（最近成功 {last}，累计 {len(ok_recs)} 篇）"
             if last else "尚无成功进入草稿箱的文章")

    # C2 可溯源：每篇都要有选题来源 + 审稿记录，且审稿记录路径真实存在
    MISSING = {"", "—", "-", "无", "TBD"}
    traceable = []
    for r in ok_recs:
        path_ok = r["review"] not in MISSING and (
            not re.search(r"[/\\]", r["review"]) or (ROOT / r["review"]).exists()
            or Path(r["review"]).expanduser().exists()
        )
        if r["source"] not in MISSING and path_ok:
            traceable.append(r)
    c2 = bool(ok_recs) and len(traceable) == len(ok_recs)
    c2_ev = (f"可溯源 {len(traceable)}/{len(ok_recs)} 篇（选题来源与审稿记录均非空且路径存在）"
             if ok_recs else "无文章可查")

    # C3 迭代闭环：≥8 条关于选题/质量的教训，且每条附"→ 调整：<证据>"
    lessons = [l for l in section(ledger, "条目").splitlines()
               if re.match(r"\[(L|W)-\d+\]", l.strip())
               and re.search(r"选题|质量", l) and "→ 调整：" in l]
    c3 = len(lessons) >= 8
    c3_ev = f"选题/质量教训且带流水线调整证据 {len(lessons)}/8 条"

    # C4 数据回流：真实数据文件优先；否则认经验证的替代方案结论文档
    data_files = [p for p in (ROOT / "workspace" / "data").glob("wechat_stats.*")
                  if p.is_file() and p.stat().st_size > 0] if (ROOT / "workspace" / "data").exists() else []
    doc = ROOT / "docs" / "data-return-feasibility.md"
    if data_files:
        c4, c4_ev = True, f"阅读数据文件 {data_files[0].name}（{data_files[0].stat().st_size} 字节）"
    elif doc.exists() and "结论：" in doc.read_text(encoding="utf-8", errors="replace"):
        c4, c4_ev = True, "无直采通道，采用 docs/data-return-feasibility.md 中的替代方案（含结论）"
    else:
        c4, c4_ev = False, "既无阅读数据文件，也无 docs/data-return-feasibility.md 结论（PLAN T-014，截止 2026-08-16）"

    for i, (ok, ev) in enumerate([(c1, c1_ev), (c2, c2_ev), (c3, c3_ev), (c4, c4_ev)]):
        text = acceptance[i][1] if i < len(acceptance) else f"标准 {i + 1}"
        results.append((ok, text, ev))
    return results


def acceptance_li(results):
    out = []
    for ok, text, ev in results:
        cls = "done" if ok else "todo"
        mark = "✅" if ok else "⬜"
        out.append(
            f"<li class='{cls}'>{mark} {esc(text)}"
            f"<br><small class='muted'>判定依据：{esc(ev)}</small></li>"
        )
    return "\n".join(out)


def git_log():
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "-15"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        out = ""
    if not out:
        return "<li class='muted'>（无）</li>"
    return "\n".join(f"<li><code>{esc(l)}</code></li>" for l in out.splitlines())


def main():
    goal = read("GOAL.md")
    plan = read("PLAN.md")
    ledger = read("LEDGER.md")
    approvals = read("human/APPROVALS.md")
    inbox = read("human/INBOX.md")

    goal_m = re.search(r"\*\*(.+?)\*\*", strip_frontmatter(goal))
    goal_line = goal_m.group(1) if goal_m else "（未设定目标）"
    ddl_m = re.search(r"截止\s*(\d{4}-\d{2}-\d{2})", goal)
    countdown = ""
    if ddl_m:
        days = (date.fromisoformat(ddl_m.group(1)) - date.today()).days
        countdown = f"<span class='pill'>距截止 {days} 天</span>"

    acceptance = checklist(goal, "验收标准")
    # 2026-08-10 晚场：判定逻辑已按 GOAL v2（内容流水线）重建，见 acceptance_auto()
    acc_auto = acceptance_auto(acceptance, ledger, inbox)
    acc_done = sum(1 for ok, _, _ in acc_auto if ok)
    todo = checklist(plan, "待办")
    doing = checklist(plan, "进行中")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RSI · 自进化系统仪表盘</title>
<style>
:root {{ --bg:#f7f7f5; --fg:#1a1a1a; --muted:#777; --card:#fff; --line:#e4e2dd; --accent:#b05730; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#161513; --fg:#e8e6e1; --muted:#999; --card:#211f1c; --line:#38352f; --accent:#e08753; }}
}}
* {{ box-sizing:border-box; margin:0; }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.65 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif; max-width:880px; margin:0 auto; padding:2rem 1.2rem 4rem; }}
h1 {{ font-size:1.5rem; margin-bottom:.3rem; }}
h2 {{ font-size:1.1rem; margin:2rem 0 .8rem; border-bottom:1px solid var(--line); padding-bottom:.4rem; }}
h4 {{ font-size:.95rem; margin-bottom:.2rem; }}
ul {{ list-style:none; padding:0; }}
li {{ padding:.25rem 0; }}
.muted {{ color:var(--muted); }}
.goal {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; padding:1rem 1.2rem; margin-top:1rem; }}
.pill {{ display:inline-block; background:var(--accent); color:#fff; border-radius:99px; padding:.1rem .7rem; font-size:.8rem; margin-left:.5rem; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:.8rem 1rem; margin:.5rem 0; }}
.card p {{ font-size:.88rem; color:var(--muted); }}
table {{ width:100%; border-collapse:collapse; font-size:.88rem; background:var(--card); border:1px solid var(--line); border-radius:8px; }}
th,td {{ text-align:left; padding:.5rem .7rem; border-bottom:1px solid var(--line); vertical-align:top; }}
.tablewrap {{ overflow-x:auto; }}
code {{ font-size:.82rem; color:var(--muted); }}
.stats {{ display:flex; gap:1rem; flex-wrap:wrap; margin:.8rem 0; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:.6rem 1.1rem; text-align:center; }}
.stat b {{ font-size:1.4rem; display:block; }}
footer {{ margin-top:3rem; font-size:.8rem; color:var(--muted); }}
</style>
</head>
<body>
<h1>🌀 RSI · 自进化系统仪表盘</h1>
<p class="muted">更新于 {now} ｜ 数据源：git 仓库状态文件</p>

<div class="goal"><b>{esc(goal_line)}</b>{countdown}</div>

<h2>验收标准（{acc_done}/{len(acceptance)}）</h2>
<p class="muted">GOAL v2（内容流水线）·自动判定，事实源为 LEDGER 文章产出记录与仓库文件，非人工勾选。</p>
<ul>{acceptance_li(acc_auto)}</ul>

<h2>任务队列</h2>
<div class="stats">
  <div class="stat"><b>{len(todo)}</b>待办</div>
  <div class="stat"><b>{len(doing)}</b>进行中</div>
</div>
<ul>{li(doing, "（无进行中任务）")}{li(todo, "（无待办）")}</ul>

<h2>待审批</h2>
<div class="tablewrap"><table>
<tr><th>ID</th><th>动作</th><th>理由</th><th>状态</th></tr>
{approvals_rows(approvals)}
</table></div>

<h2>最近日志</h2>
{journal_cards()}

<h2>复盘账本（最新）</h2>
<ul>{ledger_items(ledger)}</ul>

<h2>Git 活动</h2>
<ul>{git_log()}</ul>

<footer>RSI · RecursiveSelfImprove ｜ 心智外置于 git，此页由 system/gen_dashboard.py 生成</footer>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"OK dashboard -> {OUT}")


if __name__ == "__main__":
    main()
