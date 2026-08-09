---
title: "RSI 自进化智能系统设计（v1）"
date: 2026-08-09
draft: false
tags: [agent, self-improvement, architecture, spec]
summary: "单 Agent + 文件状态机的自进化系统：本地定时早晚双会话，git 仓库外置心智，飞书简报+审批介入，jerryai.cn 仪表盘，分层可变性防自毁，周审防自嗨。"
---

# RSI（RecursiveSelfImprove）自进化系统设计 v1

## 0. 需求对齐结论

| 维度 | 决策 |
|------|------|
| 目标类型 | 构建/工程型 + 外部世界指标型的组合 |
| 首个目标 | 框架优先，自带试运行小目标（见第 6 节） |
| 运行载体 | 本地 launchd 定时唤起 `claude` CLI 无头会话 |
| 会话节奏 | 早晚两场短会话（早：规划+执行；晚：复盘+进化） |
| 人机接口 | 飞书简报+回复介入（主）、本地 Markdown 文件（事实源）、jerryai.cn 仪表盘（可视化） |
| 自主边界 | 内部动作（改策略/写代码/跑实验/写日志）全自主；一切外发动作（发布、部署上线、花钱）须人工审批 |

## 1. 核心架构：单 Agent + 文件状态机

Agent 无状态。系统的全部心智外置为本仓库中的 Markdown 文件；每场会话被 launchd 唤起后读文件恢复记忆，完成工作后把新状态写回文件并 commit，然后退出。git 历史即演化史，任何一天的系统状态都可回溯、可 diff、可回滚。

```
RecursiveSelfImprove/
├── GOAL.md              # 目标 + 验收标准 + 截止条件 —— 仅人可改
├── STRATEGY.md          # 当前策略与假设 —— 系统可自改（须留证据）
├── PLAN.md              # 任务队列（待办 / 进行中 / 已完成）
├── LEDGER.md            # 复盘账本：跨天累积的教训与规律
├── journal/             # 每日双日志：YYYY-MM-DD-am.md / -pm.md
├── human/
│   ├── INBOX.md         # 人的指令入口（飞书回复经 CC-Connect 也落这里）
│   └── APPROVALS.md     # 外发动作审批队列
├── workspace/           # 目标的工作产物（代码、实验、数据）
├── dashboard/           # 生成的静态仪表盘站点
├── docs/                # 设计文档与实现计划
└── system/
    ├── prompts/         # morning.md / evening.md / weekly.md 会话协议
    ├── run.sh           # launchd 调用入口（超时、锁、告警）
    └── launchd/         # com.user.rsi-am.plist / com.user.rsi-pm.plist
```

### 分层可变性（宪法 / 法律 / 政策）

自进化系统最大的内生风险是"把自己改坏"和"目标漂移"。用三层可变性隔离：

1. **宪法层：`GOAL.md`** —— 只有人可以修改。系统每场会话必读，但对它只读。
2. **法律层：`system/prompts/`** —— 核心循环协议。系统不可直接修改；若系统认为协议本身需要进化，把修改提案写入 `APPROVALS.md` 走人工审批。
3. **政策层：`STRATEGY.md` / `PLAN.md` / `LEDGER.md`** —— 完全自主修改，唯一约束：每次修改 STRATEGY 必须在当天 journal 中写明"改了什么、依据什么证据"。

## 2. 每日循环

### 早场（默认 07:30 · 规划+执行）

1. 读 `human/INBOX.md`，处理新指令并标记已读（指令优先级高于既有计划）
2. 读 GOAL / STRATEGY / PLAN / LEDGER，恢复上下文
3. 从 PLAN 领取 1–3 个任务（可按需 fan-out 子 agent 并行）
4. 执行，产物写入 `workspace/`
5. 写 `journal/YYYY-MM-DD-am.md`（做了什么、结果、遇到的问题）
6. `git commit`

### 晚场（默认 21:30 · 复盘+进化）

1. 对照 GOAL 的验收标准评估当天产出 —— 结论须附证据（测试输出、可访问的 URL、数据），禁止无证据的进展声明
2. 更新 PLAN（关闭完成项、补充新任务）
3. 复盘写入 LEDGER（错误、规律、可复用打法）
4. 如有依据，修改 STRATEGY（按政策层约束留证据）
5. 需要外发的动作追加到 `APPROVALS.md`（状态 pending）
6. 生成飞书简报并推送（经 lark-cli / CC-Connect）
7. 重建 `dashboard/` 并发布
8. `git commit && git push`

### 周审（周日晚场加强版 · 防自嗨锚点）

派遣一个独立的怀疑者子 agent，仅输入本周全部 journal 与 GOAL，任务是证伪：找出无证据的进展声明、偏离 GOAL 的策略漂移、LEDGER 中重复出现却未被修复的错误。结论写入 LEDGER 并在周报中如实呈现。此环节为结构性必选项，不可被系统跳过或弱化。

## 3. 人机接口

- **飞书简报**（晚场推送，四段固定格式）：今天做了什么 / 卡在哪 / 明天计划 / 待审批项。
- **介入三通道**：
  1. 回复飞书消息 → 经 CC-Connect 落进 `INBOX.md`，下一场会话生效；
  2. 直接编辑 `INBOX.md` 或任何文件；
  3. 随时打开 Claude Code 交互会话讨论，结论写回文件。
- **审批协议**：`APPROVALS.md` 每项含 `ID / 动作描述 / 理由 / 状态(pending|approved|rejected)`。人在飞书回复"批准 #N"或直接改状态字段；系统只执行 `approved` 项，执行后标记 `done` 并在 journal 留痕。
- **仪表盘**：静态 HTML（无构建依赖），展示目标进度、指标曲线、最近日志、待审批项、LEDGER 摘要。发布到 `rsi.jerryai.cn`，采用 GitHub Pages + CNAME：纯静态、push 即发布，Mac 休眠不影响公网可访问性（Cloudflare tunnel 依赖本机在线，会破坏第 6 节验收标准第 1 条，故不选）。

## 4. 可靠性与停机

- `run.sh` 职责：2400 秒超时（覆盖 ≤30 分钟会话并留缓冲）、stdout/stderr 落盘到 `system/logs/`、失败经飞书告警（复用 health_check.sh 模式）、锁文件防早晚场重叠。
- 会话崩溃无损状态：文件与 git 历史完整，下一场会话自然接续。
- **停机条件**写在 GOAL.md：达到验收标准，或到达截止日期。触发后系统在简报中宣布完结、停止领取任务；卸载 launchd 定时器属外发动作，走审批。

## 5. 成本预算

早晚各一场 ≤30 分钟无头会话，使用现有 Claude 订阅额度；子 agent fan-out 仅在早场任务需要时发生。无新增云服务成本（tunnel 与飞书链路均为存量设施）。

## 6. 试运行小目标（框架的第一个租户）

> **14 天内，让本框架自己的仪表盘在 rsi.jerryai.cn 上线，且数据真实。**

验收标准（写入 GOAL.md）：

1. URL 公网可访问；
2. 仪表盘展示的日志、进度、审批数据与 git 仓库实际记录一致；
3. 飞书简报连续 7 天正常送达；
4. 至少完成一次"飞书回复 → INBOX → 下场会话执行"的介入闭环。

选择理由：验收客观、工作量适中、递归纯粹——系统的第一个目标就是建成自己的可观测性，跑通它即压测了早晚循环、审批流、飞书链路的每一环。

## 7. 明确不做（v1 边界）

- 不做多 Agent 常设角色拓扑（Planner/Executor/Reviewer 分立）——单会话内按需 fan-out 已覆盖并行需求；
- 不做常驻进程与实时事件响应——介入延迟半天可接受，运维成本不可接受；
- 不做自适应预算调度——先用固定早晚节奏跑出基线；
- 不做系统自改核心 prompt 的直接权限——须走审批。

以上任何一条在真实运行暴露瓶颈后，按"可逆性仲裁"原则重新评估。
