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
| A-001 | 将本仓库 github.com/silvere/RecursiveSelfImprove 转为 public | GitHub Pages 免费版要求公开仓库；仓库内容为系统状态文件，无密钥（已 .gitignore 日志） | done（2026-08-10 批准并执行，`gh repo view` 返回 PUBLIC） |
| A-002 | 启用 GitHub Pages（经 Actions workflow 部署 dashboard/ 目录——Pages 分支模式只支持 / 与 /docs，故用 workflow 达成同一目的）并在 Cloudflare 给 jerryai.cn 添加 CNAME 记录 rsi → silvere.github.io | 达成 GOAL 验收标准第 1 条：rsi.jerryai.cn 公网可访问 | approved·执行中（Pages 已部署且域名已绑定；**剩 Cloudflare 添加 CNAME 一步，本机无 CF API 凭证，需人操作**：DNS 记录 `rsi` CNAME `silvere.github.io`，先关代理/灰云以便 GitHub 签发证书） |
