---
title: "职业规划证据包 A — 从代码作品倒推（~/Code 全量扫描）"
date: 2026-08-14
draft: true
tags: [rsi, career, evidence]
summary: "revealed preference 方法：扫描 ~/Code 全部项目的 README/CLAUDE.md + git 活跃度，倒推真实精力分布、能力证据与放弃模式。自有 commit ≈1080 条，前 5 项目占 86.8%。"
---

# 证据包 A：代码作品

> 采集时间 2026-08-14 s1 场，方法：逐项目读 README/CLAUDE.md/AGENTS.md + `git log --since=2026-02-01` 统计。
> **本文件是证据，不是结论。** 结论在 `report.md`，须与证据包 B（写作）交叉后才成立。

## A. 精力分布（自有 commit ≈ 1080 条）

| 排名 | 项目 | commit | 占比 | 累计 |
|---|---|---|---|---|
| 1 | AIWriter | 578 | 53.5% | 53.5% |
| 2 | LLMEvaluationWiki | 163 | 15.1% | 68.6% |
| 3 | Tryimage2 | 141 | 13.1% | 81.7% |
| 4 | Jerry-Skills | 28 | 2.6% | 84.3% |
| 5 | BooksReader | 27 | 2.5% | **86.8%** |

**关键二次解读**：AIWriter 的 578 条里 471 条（81%）作者是 `AIWriter Bot`/`Claude`；LLMEvaluationWiki 的 163 条里 126 条精确落在每天 09:0x（cron）。**排名第 1、2 的项目，多数提交不是他敲的，是他建的系统自己跑出来的。** 换算成人手实际投入：AIWriter ~107、LLMEvalWiki ~37、Tryimage2 141、RSI 25、BooksReader 27。

**作息证据**：AIWriter 提交时间双峰——00-01 点（164 条）与 07-09 点（179 条）。深夜手工开发 + 早晨定时机器跑，典型"白天有工作、靠早晚两头维持副业系统"。RSI 直接把这个作息固化成 launchd 定时会话。

**持续投入的三类**：①内容生产流水线（AIWriter/AIWriter2/Tryimage2/wtqn/AIRedBook/RedBookReader）②知识资产站点化（LLMEvaluationWiki 1475 条 / BooksReader 24 站 / ResearchPages 11 站 / ModelThinking 118 模型 / StonePu 250+）③让 ①② 自动跑的 Agent 编排与个人基建（RSI / 39 个 skill / 30+ launchd / 15 个 jerryai.cn 子域）。其余全是一次性冲刺。

## B. 重要修正：非本人代码

| 项目 | 真相 |
|---|---|
| paseo | 他人开源项目 clone，2297 commits 他 0 条 |
| nexus4cc | fork，279 commits 他仅 1 条 |
| Agent-Reach | clone 他 0 提交，但写了本地 CLAUDE.md + 314 行 skill 供自己调用 |
| research/openclaw | 非 git 的第三方 TS Agent 平台，用于阅读/集成 |

## C. 能力证据（每条附支撑文件）

- **C1 Agent 编排与自主系统设计（最强项）**：RSI 的分层可变性（宪法层 GOAL.md 仅人可改／法律层 system/prompts 提案审批／政策层 STRATEGY/PLAN/LEDGER 自主）把宪政结构映射到 Agent 权限边界。且设计了**反自欺验收**——L-007 记载"可溯源"判定不只查字段非空、还查路径在磁盘真实存在，因为"会话写个不存在的路径就能把标准点亮"。**给自己的 Agent 设计反作弊验收，是评测人思维，不是开发者思维。**
- **C2 评测方法论（最被低估）**：`agent-eval-notes/agent-trajectory-system-design.md` 是全 workspace 唯一像专业交付物的文档——双轨记录（声明流／效应流物理分离）、配置内容寻址、扁平 append-only 事件流；引 AgentGUI（arXiv:2607.26300）实测说明"4B 无干预打不过 2B，加一次 audit 后排序恢复单调"，立论"分数是 harness 的函数，不是模型的函数"。**并主动标注论据边界**："单一任务、单一模型族、N=50，排序翻转的存在性可信、普适性未经证明"——这条纪律全 workspace 只在此文档与 LLMEvaluationWiki 出现。
- **C3 工程判断力沉淀**：LEDGER L-015（"请求时就别要"优于"下载后转格式"）、L-016（逃生开关只覆盖一半路径 = 没有开关）、L-008（自杀式调度事故）。`health_check.sh` 注释："2026-07-25 起 Caddy 挂了 18 天无人知晓"。**他反复被同一类问题咬：静默失败；也反复在同一类问题上产出最好的洞察。**
- **C4 零依赖静态站规模化**：BooksReader 24 站/166 html、ResearchPages 11 站/73 html、ModelThinking 722KB 内嵌数据全部无构建无依赖。会把成功产出模式抽象成 SOP → 做成 skill（/book、/rp）→ 批量复制。**这是流程设计能力，不是前端能力。**
- **C5 全栈产品化速度（仅冲刺时）**：XXOKR = Next.js+Prisma+Playwright+Vitest、175 个 ts/tsx、组织树/五态状态机/对齐成环检测，README 称六阶段全交付，线上 okr.jerryai.cn——**git log 显示从 Initial commit(09:40) 到最后一条(21:47) 只有 5 条提交、12 小时。**
- **C6 个人基建运维**：30+ launchd、15 个 jerryai.cn 子域、Cloudflare named tunnel、Caddy、PM2、postgres、redis、self-hosted GitHub Actions runner。
- **C7 组织语境（推断，高置信）**：39 个 skill 里 25 个是 `lark-*`；git 作者名 `sunjingwei.jerry`；有 `byteVerse/`；XXOKR"对标飞书 OKR"；myOwnDrama"对齐飞书短剧 Agent MVP 技术方案与 PRD"。→ 在以飞书为工作台的公司（大概率字节）任职，岗位接触 Agent 产品评测。

## D. 放弃模式（起了大摊子却停了）

| 项目 | 摊子 | 停在哪 |
|---|---|---|
| XXOKR | 生产级 Next.js，175 文件，e2e+smoke 两套测试 | **建成当天停**（2026-08-01），此后 0 提交 |
| ShooterGame | Godot 4 全套 EventBus/对象池/数据驱动，166 文件，有 spec+plan+gdUnit4 | **21 条提交全在 2026-07-04 一天** |
| myOwnDrama | 3.8 GB，7 模块 orchestrator + 多 adapter，对齐正式 PRD | 4 月停（疑与工作项目绑定，方向变即死） |
| StonePu | 137 md + 159 html，自研抽取脚本，2.5 GB | 5-7 月三个月仅 6 条提交 |
| CoffeeExpert | 四飞轮架构 + FSRS 间隔重复 + 技能树 YAML | 7 条提交，线上活着但内容不长 |
| AIWriter2 | 定位 AIWriter 继任者，RSI GOAL 明写要复用 | **仅 5 条提交；L-006 记载它与 wechat-sync 产物路径根本对不上——继任者没建成，前任还在扛全部产能** |
| AIRedBook/RedBookReader | 完整小红书运营 SOP：账号定位/5 类模板/周工作流/关键词库 | **非 git，无一篇产出记录——纯"想做"** |
| 8 个空目录 | HowToAsk/LocalLLM/Rasberry/RemoteCodex/RemoteControl/doubao/hermes/jerryAI | 0 字节，起名即完成 |

**三条规律**：
1. **"从 0 到能跑"效率极高、动力极强；"从能跑到有人用"动力归零。** 停滞项目的共同点不是难度，是**缺少外部需求拉动**（XXOKR 一天建成后再没打开，因为没有团队在用）。
2. **放弃代码，但不放弃服务。** 停滞项目全配了 launchd + 子域常驻——"停滞"= "冻结成资产挂着"。15 个子域是 15 座他不再走进去、但坚持交电费的房子。
3. **越靠近发布/变现，完成度越低。** AIRedBook 零产出；`money` skill 的 validate 是"搜索真实付费证据"而 stock 标着"预留 🔜"；RSI 的 GOAL 边界写死"草稿箱全自主、实际发布始终由人点击"。**整条流水线做到草稿箱为止，最后一厘米一直没跨过去。**

## E. 与 3-5 年方向相关的非显然信号

- **E1 真正的产品是"元层"，而且他还在往上爬。** 写文章 → 建 AIWriter 自动写 → 建 AIWriter2 改进质量 → 建 RSI 自动改进 AIWriter2；还有 `lark-skill-maker`（造 skill 的 skill）。**每解决完一层就立刻搬到上一层，而不把这一层做深。** 这解释了 D 中全部停滞：不是没耐心，是抽象层级上瘾。既是稀缺天赋（真会做 Agent 架构的人很少），也是最大风险（永远交付不出一个"完成"的东西）。
- **E2 阅读与建造是同一件事——控制论。** BooksReader 24 本选书极不随机：控制论、VSM（Beer 可存活系统模型）、自由能、因果推断、贝叶斯、机制设计、决策理论、算法信息论、组织权力。而 RSI 本身就是教科书式控制回路：GOAL=setpoint、LEDGER=积分器（只增不删）、watchdog=监督器、gen_dashboard=反馈测量、分层可变性=Beer 的递归系统层级。**01 号书就是《控制论》且带交互式负反馈模拟器。这是一个人用多年从多方向逼近同一问题：如何设计一个能自己变好的系统。**
- **E3 最有市场差异化的能力，恰是投入最少的那个。** `agent-eval-notes` 只有 4 条 commit，却是唯一对外拿得出手的方法论交付物；LLMEvaluationWiki 1475 条自动日更三个月不断。**"Agent 产品评测"赛道极缺人、极缺方法论，他已有素材库 + 能立论的设计文档 + 自己搭 harness 的实操经验（RSI 就是他自己的被测对象）。而他把 53% 产能放在写公众号文章上——这是最明显的错配。**
- **E4 给 Agent 设计反作弊验收的直觉值钱。** L-007、L-010（"验收判定悄悄失效，比判错更危险，因为它看起来正常"）、轨迹设计文档的"静默失败检测"、health_check.sh 的"18 天静默故障"。**他反复独立撞上并命名了同一个问题：可观测性缺口下的静默失败——这正是 Agent 评测当前最核心、最没被解决的问题。他有第一手痛感，多数做评测的人只有二手框架。**
- **E5 完全没有协作信号——最大结构性短板。** 自有仓库无一条他人 commit、无 PR、无 issue、无 co-author、无 stars；三个有社区热度的仓库全是别人的。RSI 的人机接口是"人在飞书对自己造的机器人说话"——**连协作对象都是他自己造的。3-5 年内 Agent 领域价值分配高度依赖"被别人使用/引用/采纳"，技术能力不是瓶颈，分发和协作是。**
- **E6 时间结构已把答案说出来。** 他用工程手段把下班后可支配时间压榨到极限——让机器在他上班和睡觉时替他干活。**这个结构能再撑一两年，天花板不是技术，是他本人只剩早晚两个窗口。** 且他在给业余系统设 OKR 和停机条件（GOAL 的 30 天 / 4 条验收 / 未达成则等待裁决），更像在给"要不要 all-in"做一次有截止日期的实验。
- **E7 反向信号**：给变现建了入口（money skill）、建了验证器（validate = 搜索真实付费证据），但没建执行器。**态度是"先证明它值得做"而非"先做了再说"——评测人格的又一次显影，也是至今没有外部收入回路的原因。**
