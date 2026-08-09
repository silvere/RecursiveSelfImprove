---
title: "APPROVALS — 外发动作审批队列"
date: 2026-08-09
draft: false
tags: [rsi, human]
summary: "一切外发动作在此排队，approved 后系统才执行。"
---

# 审批队列

> 条目格式如下。人审批方式：直接把状态改为 `approved`/`rejected`，或在飞书回复"批准 A-001"。系统只执行 approved 项，执行完标 `done` 并在 journal 留痕。

| ID | 动作 | 理由 | 状态 |
|----|------|------|------|
| A-001 | 将本仓库 github.com/silvere/RecursiveSelfImprove 转为 public | GitHub Pages 免费版要求公开仓库；仓库内容为系统状态文件，无密钥（已 .gitignore 日志） | pending |
| A-002 | 启用 GitHub Pages（分支 main，目录 /dashboard）并在 Cloudflare 给 jerryai.cn 添加 CNAME 记录 rsi → silvere.github.io | 达成 GOAL 验收标准第 1 条：rsi.jerryai.cn 公网可访问 | pending |
