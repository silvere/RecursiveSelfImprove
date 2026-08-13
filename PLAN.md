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

- [ ] T-012 **选题入口接 wtqn**：每日从 wtqn 问题库取 3 条候选，落地为 `workspace/topics/YYYY-MM-DD.md`（含来源链接），供当日成稿选用 ｜验收：连续 2 天有候选文件且每条可回溯到 wtqn 原始条目（服务 GOAL 验收第 2 条"可溯源"）｜**进度（08-14 s2）：第 1 天已达成** — `workspace/topics/2026-08-14.md` 3 条候选均带 `talk_id/source_url/question_idx`，当日文章即取自候选 1；库真实位置是 Obsidian `Silvere/AI-Articles/Question-Bank/`（236 条），**不在 `~/Code/wtqn/data`**（该目录不存在）｜剩余：08-15 再跑一次即闭环；建议顺手脚本化取候选这一步，别每天现查路径｜已知空洞：抓取管线自 2026-04-27 无新增，`sources/podcast`、`sources/substack` 均 0 条
- [ ] T-013 **一键化 `system/pipeline/run_daily.sh`**：把 T-010 的手工步骤串成一条命令，失败即中止并报错到简报 ｜验收：连跑 2 天，会话只需执行一条命令 + 人工审校
- [ ] T-015 **七刀审稿记录归档规范**：定义每篇文章的审稿痕迹存放路径与最小字段（选题来源／论点竞技场结论／七刀修改），使 GOAL 验收第 2 条可机器检查 ｜验收：gen_dashboard 的 C2 判定能读到该路径并给出可溯源篇数

## 进行中

- [ ] T-019 **两日专题：AI 时代 3-5 年职业规划分析报告**（人 08-13 下达，08-15 晚场交付，每场 ≤50% 预算）｜进度：证据采集已完成（`workspace/career-2026/evidence-code.md` 从 ~1080 条自有 commit 倒推精力分布与放弃模式；`evidence-writing.md` 从 456 篇写作倒推主题聚类与未闭合命题）｜下一步：待人答复 6 项关键输入（职级与平台资源／收入底线与风险承受度／心流与耗竭分布／期望的被需要方式／家庭地域约束／外部筹码），先写 2~4 条路线的骨架与"关键假设/第一年验证动作/放弃信号"，人答复后交叉打分 ｜**进度（08-14 s2）：骨架已完成** — `workspace/career-2026/routes-draft.md` 4 条赌注互斥的路线（A 评测标准定义权／B 独立验收方法论／C 内容基础设施产品化／D 脱钩写作资产），每条含可证伪假设＋第一年验证动作＋可观察放弃信号，按"人未答复"口径**刻意不排序**，末段写明 6 项待答输入各取值如何影响排序 ｜下一步：08-15 成文交付；**最该追问的一项已定位**——"Agent 轨迹系统设计稿是合规不允许对外，还是根本没试过"，它单独决定 A 与 B 的相对位置 ｜验收：报告存 Obsidian `Silvere/AI-Articles/`（日期前缀），简报给摘要

## 已完成

- [x] T-014 **数据回流可行性结论**（2026-08-14 s2，早于 08-16 截止）｜**结论：官方 API 路径不可行，阻塞点是账号资质不是工程** ｜验收达成：`docs/data-return-feasibility.md` 给出明确二选一结论 + 被拒证据 + 代理方案 ｜**实测对照证据（同一 access_token 下）**：`cgi-bin/draft/count` → `{"total_count": 96}` 成功，而 `datacube/getarticlesummary`／`getarticletotal`／`getusersummary`／`getusercumulate`／`freepublish/batchget` 全部 `{"errcode":48001,"errmsg":"api unauthorized"}`——凭证有效、链路通畅，唯独数据类权限位没开，据此判定为**未认证订阅号**（官方文档载 `getarticlesummary` 限「仅认证」）｜代理方案：主通道人工周度抄录后台阅读数 → `workspace/metrics/wechat-reads.csv`（5-8 分钟/周，延迟 ≤7 天）；辅通道 Pages 镜像站接 Cloudflare Web Analytics（一次性 20 分钟，此后 0 人工，但与公众号阅读的相关性**标注为未验证推测**，需 8 周双轨数据检验）｜**已实测否决**：GitHub `repos/.../traffic/views` 返回 `count=0`，统计的是仓库页而非 Pages 站点，不能当代理指标 ｜**顺带查实**：`wechat.py::publish_draft()` 在生产链路中从未生效过——系统一直无发布权限，群发始终由人手动点击（与 GOAL 约定一致）｜**待人回答一个问题**（不影响结论，只影响未来是否值得花 300 元/年）：该公众号是企业还是个人主体？个人主体无法微信认证，此路永久封死；企业主体认证后 API 全自动打通，改造约 1 小时。主体类型 API 读不到，需登录后台「设置与开发 → 账号详情」看一眼

- [x] T-018 **修调度挂死与锁死连锁**（2026-08-14 s1，事故驱动，非计划内）｜验收达成：看门狗实测本该跑 120s 的进程 4s 被杀且 RC=142；锁的 4 场景用生产函数体实测全对 ｜证据：`system/run.sh`（超时改 wall-clock 看门狗 + 锁加 start 时间戳与强制接管）；事故根因与可判定指标见 L-017 ｜**注意：改动对下一场（07:30）起生效，本场自身仍跑在旧版超时机制上**

- [x] T-017 **修 WebP 配图阻塞**（2026-08-13 s2）｜验收达成：`.wechat-sync.json` 的 `uploaded_image_count: 1`（原为 0），新 media_id=-Eu-2F7MukrOEiQGhnmJqxAuSYZI65ADisZwY68OQ3cJiX2JJWo6Fgs7tMCn8yNj ｜证据：CI run 31651452747 `强制模式：删除旧草稿 → ✓ media_id=... 图片1 → 汇总：同步 1 | 失败 0`；AIWriter commit 0cb9cdc（Accept 头 + 魔数兜底 + 存量图转 JPEG）、e2af4ee（--force 越过本地 marker）｜根因与两条教训见 L-015 / L-016
- [x] T-010 **端到端跑通第一篇**（2026-08-13 s1）｜证据：LEDGER"文章产出记录"首行 media_id=-Eu-2F7MukrOEiQGhnmJq7hfaBuqStdLXmtRD1EfGDqSvcAXDjVRAgvwb3tBLPrM；CI run 31624378522 输出 `汇总：同步 1 | 失败 0`；AIWriter commit bd8bd44（文章）→ 120d482（配图）→ 3ef5c6c/后续（封面修复）｜实测耗时：约 75 分钟（超单场预算 2.5 倍，全部超支花在 WebP 配图问题的 4 次 CI 往返上，见 L-012）
- [x] T-011 **转换桥 `system/pipeline/to_posts.py`**（2026-08-13 s1）｜证据：脚本 109 行，实测对 `AIWriter2/articles/2026-08-08-hobby` 产出 article.md(3,960 字符)+article.html(16,814 字符)，占位符正则匹配数 1，产物通过 wechat-sync 全流程并拿到 media_id ｜遗留：封面生成尚未纳入脚本（本次手工 sips 转换），并入 T-017

- [x] T-001 rsi.jerryai.cn 上线 ｜证据：2026-08-10 经 tunnel ingress + route dns 部署（A-001/A-002 批准当日执行），DoH 验证 HTTP 200；本地服务 cn.jerryai.rsi-dashboard（127.0.0.1:8906），备用镜像 silvere.github.io/RecursiveSelfImprove
- [x] T-002 完善仪表盘：验收标准自动打勾（v1 版）｜证据：gen_dashboard.py `acceptance_auto()`；v1 目标停用后该逻辑于 2026-08-10 晚场被 T-016 重写
- [x] T-003 演练介入闭环 ｜证据：人 2026-08-10 12:33 与 13:38 两次经飞书下达指令 → inbox_listener 实时写入 human/INBOX.md → 会话执行（第一条升级为 GOAL v2，commit b16b649；第二条路由为 A-003 提案，见本日 -pm journal）
- [x] T-004 简报送达计数器 ｜证据：gen_dashboard.py `delivery_streak()`，6 组边界用例通过（见 L-002）
- [x] T-016 重建仪表盘验收判定以匹配 GOAL v2 四条标准 ｜证据：gen_dashboard.py `acceptance_auto()` 改为读 LEDGER"文章产出记录"段：C1 连续产出天数≥14、C2 可溯源篇数/总篇数、C3 带"→ 调整："证据的选题/质量教训数≥8、C4 数据回流通道文件存在性；`python3 system/gen_dashboard.py` 退出码 0，当前如实显示 0/4（尚无产出记录）
- （建设期任务见 docs/superpowers/plans/ 与 git 历史）
