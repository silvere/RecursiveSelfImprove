---
title: "LEDGER — 复盘账本（系统可自改）"
date: 2026-08-09
draft: false
tags: [rsi, ledger]
summary: "跨天累积的教训、规律与可复用打法。"
---

# 复盘账本

> 只增不删。每条格式：`[L-NNN] 日期 ｜类别(错误/规律/打法) ｜内容 ｜证据`。周审结论也写入此处，前缀 [W-NNN]。
> **关于选题/质量的教训额外要求**（GOAL v2 验收第 3 条）：必须在条目里写 `→ 调整：<对 prompt/流程/标准的具体变更 + 证据>`，否则仪表盘不计入迭代闭环计数——只写"学到了什么"而没有改动落地，等于没学。
> **`→ 调整：` 还须绑定一个可自动判定的验收指标**（2026-08-13 s2 新增，依据 Self-Harness 的 Proposal Validation 段）：写出改动之后要说清"用什么命令/字段判定它真的有效"。理由是反例已经发生过——L-012 的 `→ 调整：`（"给 fill_images 加魔数转换"）是排障末尾凭推断写下的、未经验证，下一场一实测就发现真因在更上游的请求头，方案作废（见 L-015）。**未经验证的改进提案会以"已落地"的面目留在 PLAN 里，比没有提案更危险。**

## 条目

[L-001] 2026-08-09 ｜打法 ｜macOS 自动化脚本不可假设 GNU 工具存在（无 timeout/flock），须用 perl alarm 与 mkdir 锁替代 ｜system/run.sh 实现
[L-002] 2026-08-10 ｜打法 ｜累积指标（连续送达天数）只记原始事实行，派生数字由代码计算——晚场追加"日期｜成功/失败｜备注"即可，天数由 gen_dashboard.py delivery_streak() 推导，杜绝会话手算漂移 ｜system/gen_dashboard.py + 6 组边界用例通过
[L-005] 2026-08-10 ｜打法 ｜人的指令入口从"手改文件"升级为"飞书直接发消息"：run.sh 每场会话前调 system/pull_inbox.py 拉取 P2P 新消息写入 INBOX（message_id 去重、首跑只建检查点不回灌历史）。人只需在飞书对机器人说话 ｜system/pull_inbox.py
[L-004] 2026-08-10 ｜错误→打法 ｜本机 DNS 解析层不可信：Astrill VPN 代理（198.19.255.254）会长期缓存陈旧 NXDOMAIN，导致新上线域名在本机 curl exit 6 但公网正常。凡判定"站点是否可访问"必须以公网视角为准——http_check() 已内置 curl --doh-url https://1.1.1.1/dns-query 兜底 ｜system/gen_dashboard.py http_check()
[L-003] 2026-08-10 ｜打法 ｜仪表盘经 named tunnel 上线（launchd cn.jerryai.rsi-dashboard 在 127.0.0.1:8906 起 http.server 服务 dashboard/，tunnel ingress 转发）——dashboard/ 是实时服务目录，gen_dashboard.py 一跑完线上即更新，无需等 push；jerryai.cn 加子域的完整手册在 Claude 记忆库 cf-jerryai-subdomain-playbook ｜https://rsi.jerryai.cn HTTP 200

[L-006] 2026-08-10 ｜错误 ｜v2 流水线的第一个断点在两个仓库之间：aiwriter2 产物落在 `AIWriter2/articles/<slug>/`，而 wechat-sync 只扫 `AIWriter/posts/YYYY-MM-DD/<slug>/article.html`（其 Step 2 的 find 命令写死此路径）。此前"复用既有资产即可打通"的默认假设不成立，必须写转换桥 ｜证据：`~/.claude/commands/wechat-sync.md` Step 2；`ls AIWriter2/articles/` → 2026-07-12-ai-learning 等目录 ｜→ 调整：PLAN 新增 T-011（system/pipeline/to_posts.py），且 T-010 改为"先手工端到端跑通 1 篇暴露真实格式差异"，不先写代码
[L-007] 2026-08-10 ｜打法 ｜验收判定必须防自欺：v2 的"可溯源"判定不只检查审稿记录字段非空，还检查该路径在磁盘上真实存在（`article_records()` + `acceptance_auto()` C2）。仅检查非空的话，会话写一个不存在的路径就能把标准点亮 ｜证据：system/gen_dashboard.py；构造用例中"标题A"填了 workspace/reviews/a.md（不存在）→ 判定 0/2 可溯源

[L-009] 2026-08-12 ｜打法 ｜晚场会话遇到预算明显不够的大任务（如"跑通 aiwriter2 全流水线"，H4 未验证、乐观估计已超单场 30 分钟预算）时，不要硬冲导致烂尾，改为**侦察+沉淀**：花几分钟定位可复用的具体素材/断点（本次发现 `AIWriter2/articles/2026-08-08-hobby` 已有完整六刀审稿记录可直接拿来测试），把发现写进 PLAN 对应任务条目，让下一场不用重新搜索就能直接开工 ｜证据：本条对应的 PLAN.md T-010 更新、human/INBOX.md 处理记录
[L-010] 2026-08-13 ｜错误 ｜**LEDGER 的"文章产出记录"段一直缺 `## ` 标题行**，而 gen_dashboard.py `article_records()` 用 `section(ledger_text, "文章产出记录")` 按标题取段——也就是说，即使今天写下第一行产出记录，仪表盘也会读到空、四条验收永远显示 0/4，且没有任何报错。这是"验收判定悄悄失效"类故障：比判错更危险，因为它看起来正常 ｜证据：`grep -n "^## " LEDGER.md` 改前只返回"条目/简报送达记录"两节 ｜→ 调整：本场补回 `## 文章产出记录` 标题；后续 T-015 落地时给 gen_dashboard 加一条"段落缺失即报警"的自检，不让空段和"段不存在"共用同一个静默返回值
[L-014] 2026-08-13 ｜错误→打法 ｜**收尾时把 `git add -A && git commit --amend` 打在了别的仓库**：清理 worktree 的那条命令以 `cd /Users/jingweisun/Code/AIWriter` 开头，后面用 `;` 接了本该在 RSI 仓库执行的 amend——结果 amend 了人的在途分支 HEAD（4d64450 → 985739e）并把 30+ 个未跟踪的旧配图一并 add 进去。已用 `git reset --mixed 4d64450` 完全还原（HEAD、ahead 19、未跟踪状态均复原，未 push 出去） ｜证据：还原后 `git log --oneline -1` = 4d64450、`git status -sb` = ahead 19 ｜→ 调整：**跨仓库操作的收尾命令一律拆成独立调用，绝不用 `;`/`&&` 把"在别的仓库做的事"和"在本仓库提交"串在一行**；`git add -A` 在非本仓库目录下等于把别人的工作区一起打包，风险远高于省下的一次调用
[L-012] 2026-08-13 ｜错误→打法 ｜**配图链路的隐性类型不匹配卡死了首篇同步 4 次**：CI「自动填充文章配图」从 pexels 下载的图片实为 **WebP**，却按 `.jpg` 存盘（`file` 输出 `RIFF ... Web/P image`）；微信 `material/add_material` 按真实内容校验，返回 `errcode=40113 unsupported file type`。中间还踩了两个假线索：先以为"没有封面"（其实是 `_pick_cover` 找到了但上传被拒）、后以为是 runner checkout 竞态（重试 3 次同样报错）。最终 `sips -s format png` 转成真 PNG 并改名 `cover.png` 后一次通过 ｜证据：run 31624378522 `✓ media_id=-Eu-2F7Mukr... 汇总：同步 1 | 失败 0`；对照组 `posts/2026-08-11/meta-muse-*/cover.jpg` 真实类型是 PNG 也被接受 → 证明微信认内容不认扩展名，只拒 WebP ｜→ 调整：①PLAN 新增 T-017：给 `AIWriter/skills/scripts/fill_images.py::_download_url` 加"下载后按魔数判类型，WebP 一律转 PNG 再存"，否则每篇 pexels 配图文章都会卡住（这是 14 天连续性验收的系统性阻塞源）；②`to_posts.py` 后续接管封面时直接产 `cover.png`
[L-013] 2026-08-13 ｜错误 ｜**首篇成稿的正文图片数为 0**（`.wechat-sync.json` 的 `uploaded_image_count: 0`）：封面已上传成功，但正文里那张 `images/concept_01.jpg` 仍是 WebP，被静默跳过。也就是说草稿箱里这篇是"有封面、无正文配图"的裸文 ｜证据：同上 marker 文件 ｜→ 调整：并入 T-017 一起修（同一个根因），修完后本篇用 `--force` 重发一次验证正文图能上去
[L-016] 2026-08-13 ｜错误 ｜**逃生开关只覆盖了一半路径 = 没有逃生开关**：`sync_drafts.py --force` 的文档语义是"强制重发已同步文章"，但本地 `.wechat-sync.json` 的存在性检查排在 `--force` 分支**之前**且不看 force——于是 force 唯一的适用对象（已同步过的文章）在到达强制分支前就被筛掉了，命令静默变成空操作。第一次验证 T-017 因此白跑一轮 CI（run 31651326044：`已有标记，跳过 / 汇总：同步 0`）。**这类 bug 的共性：把"跳过"写成早退（early continue），而把"例外"写在早退之后。** ｜证据：修前 run 31651326044 同步 0；修后 run 31651452747 `强制模式：删除旧草稿 → ✓ media_id=... 图片1 → 汇总：同步 1` ｜→ 调整：commit e2af4ee 改为 `if marker.exists() and not args.force`；写法规约记此：**凡有 `--force`/`--overwrite` 类开关，所有早退分支都必须显式与它求交，不能依赖"后面还有一个 force 分支"**
[L-015] 2026-08-13 ｜规律 ｜**"下载后转格式"是补救，"请求时就别要"才是修复**：WebP 卡死链路（L-012/L-013）的真因不在下载之后，而在请求头——pexels/unsplash 的 CDN 按 `Accept` 做内容协商，头里带 `image/webp` 就返 WebP，去掉就返真 JPEG。同一个 URL 实测：带 webp 头 → `content-type: image/webp` / `file` 判 `RIFF ... Web/P image`；换成 `image/jpeg,image/png,image/*;q=0.8` → `content-type: image/jpeg` / `JPEG image data ... 940x627`。原计划（T-017 初版）是"下载后按魔数转 PNG"，那要引入 Pillow 依赖 + 一层转换代码，且每张图都多一次解码编码；改请求头是零依赖零转换。**一般化：遇到"产物格式不对"的问题，先回溯到这个格式是在哪一步被决定的——很多时候上游有一个开关，比下游加一层转换器便宜一个数量级。** ｜证据：本场 curl 对照实测（两个 Accept 头，同一 pexels URL）；修复后 `_download_url` 实测落盘魔数 `ff d8 ff e1` ｜→ 调整：`AIWriter/skills/scripts/fill_images.py` 的 `_ACCEPT_IMAGE` 常量（commit 0cb9cdc），魔数检测只作为"别的源无视 Accept"的兜底，且无 Pillow 时拒图而非放行——宁可少一张图，也不让 WebP 再流进仓库
[L-011] 2026-08-13 ｜打法 ｜**跨仓库写文章必须先看目标仓的当前分支**：AIWriter 仓库当时停在人的在途分支 `redo-ai-flavor-fix`（ahead 19 / behind 23），直接 `git commit` 会把系统的产物塞进人的未完成工作里，`git push` 也不会触发 main 上的 CI。正确做法是 `git worktree add --detach /tmp/aiw-main origin/main` + cherry-pick + `push origin HEAD:main`，再把原分支 reset 回去，全程不动人的工作区 ｜证据：本场执行序列（worktree add → cherry-pick bd8bd44 → push 82ff649..bd8bd44 → 原分支 reset 回 4d64450，`git status -sb` 恢复为 ahead 19）
[L-008] 2026-08-12 ｜错误→打法 ｜**自杀式调度变更事故**：08-11 07:30 会话执行"每 6 小时排班"改造时 `launchctl unload` 了自己所属的定时任务，当场被 SIGTERM 杀死——新定时器没装上、记账没写完、告警代码也一起死了，系统静默停摆 2 天，直到人发现"没有进展"。根因：会话感知不到"我正运行在我要卸载的东西里面"。→ 调整：①三份协议行为边界新增第 6 条"调度自保"禁令（严禁 unload/bootout/kickstart 任何 rsi-* 任务，调度变更=改文件+待外部 reload）；②run.sh 加 SIGTERM trap，被杀先发飞书告警再退出；③交互会话 2026-08-12 已代为装载 rsi-work/rsi-pm 恢复调度 ｜git 本次 commit + launchctl list 输出

## 文章产出记录

（GOAL v2 的原始事实行，派生指标由 gen_dashboard.py 计算，会话不要手写"第 N 天"）
（格式：日期 ｜标题 ｜选题来源 ｜审稿记录 ｜草稿箱：成功/失败 + media_id 或原因）

2026-08-13 ｜刷手机不欠任何人道歉 ｜aiwriter2 既有存稿（AIWriter2/articles/2026-08-08-hobby/01-brief.md，非 wtqn 选题——选题入口尚未接通，见 T-012）｜/Users/jingweisun/Code/AIWriter2/articles/2026-08-08-hobby/06-review.md ｜草稿箱：成功 media_id=-Eu-2F7MukrOEiQGhnmJqxAuSYZI65ADisZwY68OQ3cJiX2JJWo6Fgs7tMCn8yNj（08-13 s2 修 WebP 后重发，正文配图 1 张已上传；旧 media_id=-Eu-2F7MukrOEiQGhnmJq7hfaBuqStdLXmtRD1EfGDqSvcAXDjVRAgvwb3tBLPrM 的裸文草稿已删除）

## 简报送达记录

（格式：日期 ｜成功/失败 ｜备注）

2026-08-09 ｜成功 ｜建设期首发，message_id om_x100b68bd4b22e8a4dd4b8545f22372f（连续送达第 1 天）
2026-08-10 ｜成功 ｜晚场简报，message_id om_x100b68a970e20ca0dd80951ebb7d5a5
2026-08-12 ｜成功 ｜晚场简报（调度事故修复后首场），message_id om_x100b68fc75ef10a4c243b2beefbe732
