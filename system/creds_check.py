#!/usr/bin/env python3
"""Claude 登录凭证预检。

为什么需要它：2026-08-17 s1 与 2026-08-18 s1/s2/s3 共 4 场会话在 8~13 秒内以
rc=1 退出，日志尾部同一行 `401 OAuth access token has expired`。run.sh 的失败
告警确实发出去了，但内容是通用的"异常退出(exit=1)"——人看不出这条要他去终端
重新登录，于是同一堵墙一天撞三次。

墙的形状（本机实测，凭证存 macOS keychain 的 "Claude Code-credentials"）：
  accessToken       约 8 小时到期，headless 场次可自动续期，不构成故障；
  refreshToken      约 48 小时到期，且只有人交互登录一次才会续。
refreshToken 一过期，之后每 6 小时的每一场都必然空跑，直到人重新登录——这是
本系统当前唯一"机器完全无法自愈"的故障。

本脚本只读到期时间戳，绝不打印任何 token 字段。

退出码：0=健康 1=临近到期(warn) 2=已过期 3=读不到（不下结论，也不告警）
stdout 一行：STATUS|REMAIN_H|EXPIRES_LOCAL|EPOCH
  EPOCH = refreshTokenExpiresAt 原值，供调用方按"每个凭证周期只告警一次"去重。
"""
import json
import os
import subprocess
import sys
import time

WARN_H = 24.0   # 提前一天首告：人未必立刻看手机，留出 4 场的余量
URGENT_H = 8.0  # 二次升级告警：再不登录，下一场起就开始空跑

def load() -> dict:
    # 测试缝：给定文件时读文件，不碰 keychain（策略 8 要求上线前先算正常态取值）
    override = os.environ.get("RSI_CREDS_JSON")
    if override:
        with open(override) as f:
            return json.load(f)
    out = subprocess.run(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        capture_output=True, text=True, timeout=20,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError("keychain 读取失败")
    return json.loads(out.stdout)

def main() -> int:
    try:
        oauth = load().get("claudeAiOauth") or {}
        exp = float(oauth["refreshTokenExpiresAt"]) / 1000.0
    except Exception as e:
        # 读不到就闭嘴：宁可漏报也不误报——误报会训练人忽略这个告警通道
        print("UNKNOWN|||%s" % type(e).__name__)
        return 3
    remain_h = (exp - time.time()) / 3600.0
    local = time.strftime("%Y-%m-%d %H:%M", time.localtime(exp))
    epoch = str(int(exp * 1000))
    if remain_h <= 0:
        status, rc = "EXPIRED", 2
    elif remain_h < URGENT_H:
        status, rc = "URGENT", 1
    elif remain_h < WARN_H:
        status, rc = "WARN", 1
    else:
        status, rc = "OK", 0
    print("%s|%.1f|%s|%s" % (status, remain_h, local, epoch))
    return rc

if __name__ == "__main__":
    sys.exit(main())
