---
title: "RSI — RecursiveSelfImprove"
date: 2026-08-09
draft: false
tags: [rsi, agent]
summary: "自进化智能系统：单 Agent + git 文件状态机，每日早晚两场自主会话，直到达成 GOAL.md。"
---

# RSI · RecursiveSelfImprove

自进化智能系统。人设定 `GOAL.md`，系统每天早晚两场自主会话（launchd 07:30 / 21:30 唤起无头 Claude）：早场规划+执行，晚场复盘+进化+飞书简报+仪表盘更新。心智全部外置为本仓库的 Markdown 文件，git 历史即演化史。

- 设计文档：`docs/superpowers/specs/2026-08-09-self-evolving-agent-design.md`
- 实现计划：`docs/superpowers/plans/2026-08-09-rsi-v1-implementation.md`
- 人的入口：`human/INBOX.md`（指令）、`human/APPROVALS.md`（审批）
- 手动触发：`./system/run.sh morning|evening|weekly|smoke`

## 分层可变性

| 层 | 文件 | 谁能改 |
|----|------|--------|
| 宪法 | GOAL.md | 仅人 |
| 法律 | system/prompts/ | 系统提案 → 人审批 |
| 政策 | STRATEGY / PLAN / LEDGER | 系统自主（journal 留证据） |
