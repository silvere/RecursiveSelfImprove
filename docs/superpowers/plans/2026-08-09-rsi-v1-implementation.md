---
title: "RSI v1 实现计划"
date: 2026-08-09
draft: false
tags: [agent, implementation-plan]
summary: "RSI 自进化系统 v1 的分任务实现计划：骨架、会话协议、仪表盘、run.sh、launchd、飞书链路、GitHub 落地、端到端冒烟。"
---

# RSI v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成可每日自动运行的自进化系统：早晚两场无头 Claude 会话读写文件状态机，飞书简报可达，仪表盘可生成，launchd 定时就绪。

**Architecture:** 单 Agent + git 文件状态机（见 spec `docs/superpowers/specs/2026-08-09-self-evolving-agent-design.md`）。Agent 无状态，心智外置为仓库 Markdown；`run.sh` 被 launchd 唤起后以 bypassPermissions 跑 `claude -p`，会话按 `system/prompts/*.md` 协议行动。

**Tech Stack:** bash + launchd + claude CLI + python3(stdlib) 仪表盘生成 + lark-cli 飞书推送 + gh。

## Global Constraints

- 分层可变性：GOAL.md 仅人改；system/prompts/ 改动须走 APPROVALS；STRATEGY/PLAN/LEDGER 自主改。
- 外发动作（发布上线、DNS、公开仓库、花钱）一律进 `human/APPROVALS.md`，状态 approved 才执行。
- 早场 07:30 / 晚场 21:30；run.sh 超时 2400s；锁文件防重叠。
- 飞书收件人 open_id：`ou_6cc25a9ef6be867e0b986d1051f0bbaf`；发送命令 `lark-cli im +messages-send --user-id <id> --markdown <text>`（bot 身份，已验证可用性见环境检查）。
- macOS 无 `timeout`/`flock`：用 perl alarm 实现超时、mkdir 实现锁。
- 所有 .md 产出带 YAML frontmatter（title/date/draft/tags/summary）。

---

### Task 1: 仓库骨架与状态文件

**Files:** Create `GOAL.md` `STRATEGY.md` `PLAN.md` `LEDGER.md` `human/INBOX.md` `human/APPROVALS.md` `journal/.gitkeep` `workspace/.gitkeep` `dashboard/.gitkeep` `system/logs/.gitkeep` `README.md` `.gitignore`

- [ ] GOAL.md 写入试运行目标（14 天仪表盘上线 rsi.jerryai.cn）+ spec 第 6 节的 4 条验收标准 + 截止日期 2026-08-23 + 停机条件
- [ ] STRATEGY.md 初始策略（v0：先打通链路再优化内容）；PLAN.md 初始任务队列（Pages 审批后启用、仪表盘数据完善、介入闭环演练）；LEDGER.md 空账本表头
- [ ] INBOX.md 定义指令格式（`- [ ] 指令文本` 未处理 / `- [x]` 已处理）；APPROVALS.md 定义条目格式（ID/动作/理由/状态）并预置首批待批项（启用 GitHub Pages、DNS CNAME rsi.jerryai.cn）
- [ ] `.gitignore`: `system/logs/*.log`、`.DS_Store`、锁目录
- [ ] Verify: `ls` 全部存在；Commit `feat: 仓库骨架与初始状态文件`

### Task 2: 会话协议 prompts

**Files:** Create `system/prompts/morning.md` `system/prompts/evening.md` `system/prompts/weekly.md`

**Interfaces (produces):** 三份协议均以"你是 RSI 系统的当值会话"开场，声明分层可变性边界、证据纪律（进展声明必须附证据）、journal 文件命名 `journal/YYYY-MM-DD-{am,pm}.md`、commit 规范、飞书发送命令（含 open_id）。

- [ ] morning.md：INBOX 处理协议（优先于既有计划，处理后打勾）→ 读四大状态文件 → 领 1–3 任务 → 执行（产物进 workspace/）→ 写 am journal → commit。禁止：改 GOAL、改 prompts、执行未 approved 的外发。
- [ ] evening.md：证据化评估当天产出 → 更新 PLAN → 复盘写 LEDGER → 有据修改 STRATEGY（journal 留"改了什么/依据什么"）→ 外发诉求写 APPROVALS(pending) → 执行已 approved 项并标 done → 生成简报推飞书（四段：做了什么/卡在哪/明天计划/待审批）→ `python3 system/gen_dashboard.py` → commit+push。
- [ ] weekly.md：晚场协议全文之外追加周审——fan-out 一个怀疑者子 agent（仅给 GOAL+本周 journal），证伪无证据声明/策略漂移/重复未修复错误，结论写 LEDGER 并入周报。
- [ ] Verify: `grep -l "ou_6cc25a9ef6be867e0b986d1051f0bbaf" system/prompts/*.md` 三份全中；Commit `feat: 三份会话协议`

### Task 3: 仪表盘生成器

**Files:** Create `system/gen_dashboard.py` `dashboard/index.html`(生成) `dashboard/CNAME`

- [ ] gen_dashboard.py（python3 stdlib）：读 GOAL/PLAN/LEDGER/APPROVALS/journal/ + `git log --oneline -15`，渲染单文件 index.html：目标与倒计时、验收标准清单、任务统计（待办/进行中/完成计数）、最近 7 天 journal 摘要、待审批表、LEDGER 最新条目、git 活动。暗色适配、无外部依赖、移动端可读。
- [ ] CNAME 内容 `rsi.jerryai.cn`
- [ ] Verify: `python3 system/gen_dashboard.py && grep -c "rsi" dashboard/index.html` 非零，浏览器可读结构完整；Commit `feat: 仪表盘生成器`

### Task 4: run.sh 运行时

**Files:** Create `system/run.sh` `system/notify.sh`

- [ ] notify.sh：`lark-cli im +messages-send --user-id ou_6cc25a9ef6be867e0b986d1051f0bbaf --markdown "$1"`，失败仅记日志不中断。
- [ ] run.sh `<morning|evening|weekly|smoke>`：cd 仓库根；mkdir 锁（含 stale pid 检测）；日志落 `system/logs/<mode>-YYYYMMDD-HHMMSS.log`；perl alarm 2400s 包裹 `claude -p "$(cat system/prompts/<mode>.md)" --dangerously-skip-permissions`；退出码非零 → notify.sh 告警；smoke 模式用内联短 prompt 验证 claude 链路。周日晚自动切 weekly（run.sh 内 `[ "$(date +%u)" = 7 ]` 判断，launchd 只需 am/pm 两个 plist）。
- [ ] Verify: `bash -n` 通过；`./system/run.sh smoke` 真实跑通并产出日志；锁目录运行中存在、结束后释放；Commit `feat: 运行时脚本`

### Task 5: launchd 定时

**Files:** Create `system/launchd/cn.jerryai.rsi-am.plist`(07:30) `system/launchd/cn.jerryai.rsi-pm.plist`(21:30)

- [ ] 两份 plist：ProgramArguments 指向 run.sh morning/evening，WorkingDirectory 仓库根，StandardOut/ErrorPath 进 system/logs/，命名沿用 `cn.jerryai.*` 惯例
- [ ] `cp` 到 `~/Library/LaunchAgents/` 并 `launchctl load`
- [ ] Verify: `launchctl list | grep rsi` 两项在列；Commit `feat: launchd 定时`

### Task 6: GitHub 落地 + 飞书链路实测

- [ ] `gh repo create RecursiveSelfImprove --private --source . --push`（私有仓库属内部动作；转公开+Pages+DNS 已在 APPROVALS 待批）
- [ ] 实发一条飞书测试简报（系统上线通知），验证 exit 0
- [ ] Verify: `gh repo view --json url`；飞书消息送达；Commit+push

### Task 7: 端到端冒烟与首日记录

- [ ] 写 `journal/2026-08-09-pm.md`（系统诞生日志：今天建了什么、验证了什么、待批什么）
- [ ] `python3 system/gen_dashboard.py` 重新生成；commit+push
- [ ] 发正式版今晚简报到飞书（四段格式，含待审批清单）
- [ ] Verify: git status clean，`launchctl list` 两项在列，明早 07:30 首场自动运行

## Self-Review

- Spec 覆盖：架构(T1)/协议(T2)/接口(T2,T4,T6)/可靠性(T4)/仪表盘(T3)/试运行目标(T1)/审批边界(T1,T6) ✓；Pages 上线本身待审批，spec 允许 ✓
- 类型一致：journal 命名、open_id、路径在各任务间一致 ✓
- 周日 weekly 切换放 run.sh 而非第三个 plist——少一个概念 ✓
