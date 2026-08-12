---
title: "PLAN — 任务队列（系统可自改）"
date: 2026-08-10
draft: false
tags: [rsi, plan]
summary: "围绕 GOAL v2（内容流水线）重排：先打通最小端到端闭环，再提质量、再补数据回流。"
---

# 任务队列

> 格式：`- [ ] T-NNN 任务描述 ｜验收方式`。完成后移入"已完成"段并附证据。
> 2026-08-10 晚场按 GOAL v2 重排（人的 INBOX 指令①）。排序原则：**先让一篇文章走完全程，再谈每天一篇**——链路不通时优化质量是空转。

## 关键路径（v2 最小闭环）

选题（wtqn）→ 成稿（aiwriter2 七刀）→ 转换（AIWriter/posts 格式）→ 同步（wechat-sync CI）→ 记录（LEDGER 文章产出记录）

已知断点：**AIWriter2 的产物在 `AIWriter2/articles/<slug>/`，而 wechat-sync 只认 `AIWriter/posts/<date>/<slug>/article.html`**（证据：`~/.claude/commands/wechat-sync.md` Step 2 的 find 命令写死该路径；`ls AIWriter2/articles/` 为 `2026-07-12-ai-learning` 等目录）。这是 T-010 要修的第一个洞。

## 待办

- [ ] T-017 **修 WebP 配图阻塞（最高优先，阻塞 14 天连续性验收）**：给 `AIWriter/skills/scripts/fill_images.py::_download_url` 加"下载后按魔数判真实类型，WebP 一律转 PNG 再存"；修完对 `posts/2026-08-13/shua-shouji-bu-qian-daoqian` 用 `gh workflow run ... --field force=true` 重发验证 ｜验收：`.wechat-sync.json` 的 `uploaded_image_count > 0` ｜依据 L-012 / L-013
- [ ] T-012 **选题入口接 wtqn**：每日从 wtqn 问题库取 3 条候选，落地为 `workspace/topics/YYYY-MM-DD.md`（含来源链接），供当日成稿选用 ｜验收：连续 2 天有候选文件且每条可回溯到 wtqn 原始条目（服务 GOAL 验收第 2 条"可溯源"）
- [ ] T-013 **一键化 `system/pipeline/run_daily.sh`**：把 T-010 的手工步骤串成一条命令，失败即中止并报错到简报 ｜验收：连跑 2 天，会话只需执行一条命令 + 人工审校
- [ ] T-014 **数据回流可行性结论**（GOAL 验收第 4 条，人指定第一周内出结论，截止 2026-08-16）：查明公众号已发布文章阅读数能否经 API/后台导出/代理指标取得，写 `docs/data-return-feasibility.md` ｜验收：文档给出"可行（附取数命令实测输出）"或"不可行（附被拒证据）+ 经验证的代理指标方案"
- [ ] T-015 **七刀审稿记录归档规范**：定义每篇文章的审稿痕迹存放路径与最小字段（选题来源／论点竞技场结论／七刀修改），使 GOAL 验收第 2 条可机器检查 ｜验收：gen_dashboard 的 C2 判定能读到该路径并给出可溯源篇数

## 进行中

（无）

## 已完成

- [x] T-010 **端到端跑通第一篇**（2026-08-13 s1）｜证据：LEDGER"文章产出记录"首行 media_id=-Eu-2F7MukrOEiQGhnmJq7hfaBuqStdLXmtRD1EfGDqSvcAXDjVRAgvwb3tBLPrM；CI run 31624378522 输出 `汇总：同步 1 | 失败 0`；AIWriter commit bd8bd44（文章）→ 120d482（配图）→ 3ef5c6c/后续（封面修复）｜实测耗时：约 75 分钟（超单场预算 2.5 倍，全部超支花在 WebP 配图问题的 4 次 CI 往返上，见 L-012）
- [x] T-011 **转换桥 `system/pipeline/to_posts.py`**（2026-08-13 s1）｜证据：脚本 109 行，实测对 `AIWriter2/articles/2026-08-08-hobby` 产出 article.md(3,960 字符)+article.html(16,814 字符)，占位符正则匹配数 1，产物通过 wechat-sync 全流程并拿到 media_id ｜遗留：封面生成尚未纳入脚本（本次手工 sips 转换），并入 T-017

- [x] T-001 rsi.jerryai.cn 上线 ｜证据：2026-08-10 经 tunnel ingress + route dns 部署（A-001/A-002 批准当日执行），DoH 验证 HTTP 200；本地服务 cn.jerryai.rsi-dashboard（127.0.0.1:8906），备用镜像 silvere.github.io/RecursiveSelfImprove
- [x] T-002 完善仪表盘：验收标准自动打勾（v1 版）｜证据：gen_dashboard.py `acceptance_auto()`；v1 目标停用后该逻辑于 2026-08-10 晚场被 T-016 重写
- [x] T-003 演练介入闭环 ｜证据：人 2026-08-10 12:33 与 13:38 两次经飞书下达指令 → inbox_listener 实时写入 human/INBOX.md → 会话执行（第一条升级为 GOAL v2，commit b16b649；第二条路由为 A-003 提案，见本日 -pm journal）
- [x] T-004 简报送达计数器 ｜证据：gen_dashboard.py `delivery_streak()`，6 组边界用例通过（见 L-002）
- [x] T-016 重建仪表盘验收判定以匹配 GOAL v2 四条标准 ｜证据：gen_dashboard.py `acceptance_auto()` 改为读 LEDGER"文章产出记录"段：C1 连续产出天数≥14、C2 可溯源篇数/总篇数、C3 带"→ 调整："证据的选题/质量教训数≥8、C4 数据回流通道文件存在性；`python3 system/gen_dashboard.py` 退出码 0，当前如实显示 0/4（尚无产出记录）
- （建设期任务见 docs/superpowers/plans/ 与 git 历史）
