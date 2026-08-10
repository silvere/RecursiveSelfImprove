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
| A-003 | 修改 system/prompts/morning.md：把"自进化方法论调研"固化为早场固定环节（精确 diff 见下方 A-003 附录） | 人 2026-08-10 13:38 飞书指令"每天上午 8 点调研行业递归自我进化方法论并直接应用"。这是常设指令，写进 PLAN 会被当成一次性任务做完就消失，只有写进早场协议才真正常设。协议属法律层，故走审批 | pending |
| A-002 | 让 rsi.jerryai.cn 公网可访问。执行机制经人指示改为本宅标准作业：named tunnel ingress（127.0.0.1:8906 静态服务）+ `cloudflared tunnel route dns` 建 CNAME，GitHub Pages 降级为备用镜像（silvere.github.io/RecursiveSelfImprove） | 达成 GOAL 验收标准第 1 条 | done（2026-08-10 上线，DoH 独立验证 HTTP 200；操作手册已沉淀至 Claude 记忆库 cf-jerryai-subdomain-playbook） |

---

## A-003 附录：morning.md 精确 diff（待批准后由系统执行）

在「早场流程」第 3 步（领任务）之前插入新的一步，其余步骤序号顺延：

```diff
 2. **恢复上下文**：读 GOAL.md、STRATEGY.md、PLAN.md、LEDGER.md，以及昨晚的 journal（journal/ 下最新的 -pm.md）。
+3. **自进化调研（每场固定，限时 8 分钟）**：检索一条业界"递归自我改进 / agent 自我进化"的具体方法（论文、开源实现、工程博客均可），判断能否直接用于本系统。
+   - 产出写入 journal 当天条目的"自进化调研"段：来源链接 + 一句话方法概述 + 采纳/不采纳的判断与理由。
+   - **可落地的改进按分层可变性执行**：政策层（STRATEGY.md、system/ 下的工具代码、流水线脚本）直接改，改动在 journal 留证据；法律层（GOAL.md、system/prompts/）只写提案进 APPROVALS，不得自行修改。
+   - 检索无有效结果或超时：写"本场无采纳，原因 X"，不得空转，不得为凑数强行采纳。
-3. **领任务**：从 PLAN.md"待办"中选 1–3 个最能推进 GOAL 的任务
+4. **领任务**：从 PLAN.md"待办"中选 1–3 个最能推进 GOAL 的任务
```

（后续 4/5/6 步同步顺延为 5/6/7。）

**理解声明**：人所说"直接应用于自己"，系统理解为"政策层免请示"，不解除法律层审批门。若此理解有误请直接改本条为 rejected 并注明正确边界。
