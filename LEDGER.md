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

## 条目

[L-001] 2026-08-09 ｜打法 ｜macOS 自动化脚本不可假设 GNU 工具存在（无 timeout/flock），须用 perl alarm 与 mkdir 锁替代 ｜system/run.sh 实现
[L-002] 2026-08-10 ｜打法 ｜累积指标（连续送达天数）只记原始事实行，派生数字由代码计算——晚场追加"日期｜成功/失败｜备注"即可，天数由 gen_dashboard.py delivery_streak() 推导，杜绝会话手算漂移 ｜system/gen_dashboard.py + 6 组边界用例通过
[L-005] 2026-08-10 ｜打法 ｜人的指令入口从"手改文件"升级为"飞书直接发消息"：run.sh 每场会话前调 system/pull_inbox.py 拉取 P2P 新消息写入 INBOX（message_id 去重、首跑只建检查点不回灌历史）。人只需在飞书对机器人说话 ｜system/pull_inbox.py
[L-004] 2026-08-10 ｜错误→打法 ｜本机 DNS 解析层不可信：Astrill VPN 代理（198.19.255.254）会长期缓存陈旧 NXDOMAIN，导致新上线域名在本机 curl exit 6 但公网正常。凡判定"站点是否可访问"必须以公网视角为准——http_check() 已内置 curl --doh-url https://1.1.1.1/dns-query 兜底 ｜system/gen_dashboard.py http_check()
[L-003] 2026-08-10 ｜打法 ｜仪表盘经 named tunnel 上线（launchd cn.jerryai.rsi-dashboard 在 127.0.0.1:8906 起 http.server 服务 dashboard/，tunnel ingress 转发）——dashboard/ 是实时服务目录，gen_dashboard.py 一跑完线上即更新，无需等 push；jerryai.cn 加子域的完整手册在 Claude 记忆库 cf-jerryai-subdomain-playbook ｜https://rsi.jerryai.cn HTTP 200

[L-006] 2026-08-10 ｜错误 ｜v2 流水线的第一个断点在两个仓库之间：aiwriter2 产物落在 `AIWriter2/articles/<slug>/`，而 wechat-sync 只扫 `AIWriter/posts/YYYY-MM-DD/<slug>/article.html`（其 Step 2 的 find 命令写死此路径）。此前"复用既有资产即可打通"的默认假设不成立，必须写转换桥 ｜证据：`~/.claude/commands/wechat-sync.md` Step 2；`ls AIWriter2/articles/` → 2026-07-12-ai-learning 等目录 ｜→ 调整：PLAN 新增 T-011（system/pipeline/to_posts.py），且 T-010 改为"先手工端到端跑通 1 篇暴露真实格式差异"，不先写代码
[L-007] 2026-08-10 ｜打法 ｜验收判定必须防自欺：v2 的"可溯源"判定不只检查审稿记录字段非空，还检查该路径在磁盘上真实存在（`article_records()` + `acceptance_auto()` C2）。仅检查非空的话，会话写一个不存在的路径就能把标准点亮 ｜证据：system/gen_dashboard.py；构造用例中"标题A"填了 workspace/reviews/a.md（不存在）→ 判定 0/2 可溯源

[L-008] 2026-08-12 ｜错误→打法 ｜**自杀式调度变更事故**：08-11 07:30 会话执行"每 6 小时排班"改造时 `launchctl unload` 了自己所属的定时任务，当场被 SIGTERM 杀死——新定时器没装上、记账没写完、告警代码也一起死了，系统静默停摆 2 天，直到人发现"没有进展"。根因：会话感知不到"我正运行在我要卸载的东西里面"。→ 调整：①三份协议行为边界新增第 6 条"调度自保"禁令（严禁 unload/bootout/kickstart 任何 rsi-* 任务，调度变更=改文件+待外部 reload）；②run.sh 加 SIGTERM trap，被杀先发飞书告警再退出；③交互会话 2026-08-12 已代为装载 rsi-work/rsi-pm 恢复调度 ｜git 本次 commit + launchctl list 输出

（GOAL v2 的原始事实行，派生指标由 gen_dashboard.py 计算，会话不要手写"第 N 天"）
（格式：日期 ｜标题 ｜选题来源 ｜审稿记录 ｜草稿箱：成功/失败 + media_id 或原因）

（尚无——流水线未打通，见 PLAN T-010）

## 简报送达记录

（格式：日期 ｜成功/失败 ｜备注）

2026-08-09 ｜成功 ｜建设期首发，message_id om_x100b68bd4b22e8a4dd4b8545f22372f（连续送达第 1 天）
2026-08-10 ｜成功 ｜晚场简报，message_id om_x100b68a970e20ca0dd80951ebb7d5a5
