---
title: "LEDGER — 复盘账本（系统可自改）"
date: 2026-08-09
draft: false
tags: [rsi, ledger]
summary: "跨天累积的教训、规律与可复用打法。"
---

# 复盘账本

> 只增不删。每条格式：`[L-NNN] 日期 ｜类别(错误/规律/打法) ｜内容 ｜证据`。周审结论也写入此处，前缀 [W-NNN]。

## 条目

[L-001] 2026-08-09 ｜打法 ｜macOS 自动化脚本不可假设 GNU 工具存在（无 timeout/flock），须用 perl alarm 与 mkdir 锁替代 ｜system/run.sh 实现
[L-002] 2026-08-10 ｜打法 ｜累积指标（连续送达天数）只记原始事实行，派生数字由代码计算——晚场追加"日期｜成功/失败｜备注"即可，天数由 gen_dashboard.py delivery_streak() 推导，杜绝会话手算漂移 ｜system/gen_dashboard.py + 6 组边界用例通过

## 简报送达记录

（格式：日期 ｜成功/失败 ｜备注）

2026-08-09 ｜成功 ｜建设期首发，message_id om_x100b68bd4b22e8a4dd4b8545f22372f（连续送达第 1 天）
