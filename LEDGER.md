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
[L-005] 2026-08-10 ｜打法 ｜人的指令入口从"手改文件"升级为"飞书直接发消息"：run.sh 每场会话前调 system/pull_inbox.py 拉取 P2P 新消息写入 INBOX（message_id 去重、首跑只建检查点不回灌历史）。人只需在飞书对机器人说话 ｜system/pull_inbox.py
[L-004] 2026-08-10 ｜错误→打法 ｜本机 DNS 解析层不可信：Astrill VPN 代理（198.19.255.254）会长期缓存陈旧 NXDOMAIN，导致新上线域名在本机 curl exit 6 但公网正常。凡判定"站点是否可访问"必须以公网视角为准——http_check() 已内置 curl --doh-url https://1.1.1.1/dns-query 兜底 ｜system/gen_dashboard.py http_check()
[L-003] 2026-08-10 ｜打法 ｜仪表盘经 named tunnel 上线（launchd cn.jerryai.rsi-dashboard 在 127.0.0.1:8906 起 http.server 服务 dashboard/，tunnel ingress 转发）——dashboard/ 是实时服务目录，gen_dashboard.py 一跑完线上即更新，无需等 push；jerryai.cn 加子域的完整手册在 Claude 记忆库 cf-jerryai-subdomain-playbook ｜https://rsi.jerryai.cn HTTP 200

## 简报送达记录

（格式：日期 ｜成功/失败 ｜备注）

2026-08-09 ｜成功 ｜建设期首发，message_id om_x100b68bd4b22e8a4dd4b8545f22372f（连续送达第 1 天）
