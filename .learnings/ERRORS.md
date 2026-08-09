# 错误日志

[ERROR-20260809-001]
- Priority: P3 ｜ Status: Resolved ｜ Area: 权限/Bash
- Summary: auto mode 分类器拦截合并的多动作 Bash 命令（plutil+cp+launchctl、git add+commit 合并式）
- Details: 同样的动作拆成单条命令后全部放行；合并命令会提高分类器误判率
- Suggested Action: 涉及系统配置（launchctl/cp 到 ~/Library）或提交时，一条命令只做一件事
