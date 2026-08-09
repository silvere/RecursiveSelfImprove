---
title: "PLAN — 任务队列（系统可自改）"
date: 2026-08-09
draft: false
tags: [rsi, plan]
summary: "任务队列：待办 / 进行中 / 已完成。"
---

# 任务队列

> 格式：`- [ ] T-NNN 任务描述 ｜验收方式`。完成后移入"已完成"段并附证据。

## 待办

- [ ] T-001 等待"启用 GitHub Pages + 转公开仓库"审批（A-001/A-002）通过后，启用 Pages 并验证 rsi.jerryai.cn 可访问 ｜curl 返回 200 ｜堵点：A-001/A-002 仍 pending
- [ ] T-003 演练介入闭环：请人在飞书回复一条指令，验证其落入 INBOX 并在下场会话被执行 ｜journal 中有对应执行记录 ｜堵点：需人配合，等飞书回复自然触发

## 进行中

（无）

## 已完成

- [x] T-002 完善仪表盘：验收标准自动打勾（从 GOAL.md 与实际数据比对）｜证据：system/gen_dashboard.py 新增 acceptance_auto()——C1 实测 HTTP、C2 远端页面新鲜度（48h 代理指标）、C3 从 LEDGER 算连续送达、C4 数 INBOX 已处理条目；本地生成结果 0/4 与事实一致（C1 探测失败因 DNS 未配，见 2026-08-10-am journal）
- [x] T-004 简报送达计数器：在 LEDGER 中记录连续送达天数 ｜证据：gen_dashboard.py 的 delivery_streak() 从 LEDGER 原始行推导连续天数，6 组边界用例全过（空/单日/三连/中断/隔天/最新失败）；晚场只需追加原始行，天数不再手算（见 LEDGER L-002）
- （建设期任务见 docs/superpowers/plans/ 与 git 历史）
