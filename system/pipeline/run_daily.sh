#!/usr/bin/env bash
# run_daily.sh — 每日流水线一键化（T-013）+ 七刀门禁（T-020）
#
# 关键路径：选题(pick_topics) → 成稿(会话，脚本不替代) → **门禁(review_trace)** → 转换(to_posts)
#           → 提交 AIWriter/main → CI 配图+同步草稿箱 → 会话记账 LEDGER
#
# 为什么门禁在这：2026-08-14 那篇是会话赶时间直写、没走七刀，事后才被 review_trace.py 查出
# 不可溯源（见 T-020 / L-021）。靠"会话自觉在正确时刻想起来"不是机制。此后凡走本脚本，
# 三件套缺一即中止，不产出无审稿痕迹的文章。
#
# 逃生开关（L-016：force 必须与所有早退分支求交，且不能是静默的）：
#   --force-no-trace "<理由>"  跳过门禁，但理由是必填参数，且会以 gate=bypassed 落进审计日志。
#
# 审计（2026-08-15 s3 自进化调研采纳 Regimes 的"每次 promote-or-discard 都是一条事件"）：
#   每次门禁决策追加一行到 workspace/pipeline-runs.log，pass/fail/bypassed 一视同仁地留痕。
#
# 用法：
#   run_daily.sh prep  [--date YYYY-MM-DD]                 # 生成当日选题候选
#   run_daily.sh check <文章目录>                           # 只跑门禁
#   run_daily.sh ship  <文章目录> [--date D] [--slug S] [--dry-run] [--no-push]
#                                 [--force-no-trace "理由"]
#
# 退出码：0 成功 ｜ 2 用法错 ｜ 3 门禁不通过 ｜ 其它 = 被调用步骤的原始失败码

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AIWRITER="/Users/jingweisun/Code/AIWriter"
AUDIT="$REPO/workspace/pipeline-runs.log"
WT="/tmp/rsi-aiwriter-wt"

die() { echo "::error::$*" >&2; exit "${2:-1}"; }
audit() { mkdir -p "$(dirname "$AUDIT")"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$AUDIT"; }

cmd="${1:-}"; shift || true
[ -n "$cmd" ] || { sed -n '/^# 用法：/,/^#$/p' "$0"; exit 2; }

case "$cmd" in

prep)
  DATE="$(date +%F)"
  [ "${1:-}" = "--date" ] && { DATE="$2"; shift 2; }
  python3 "$REPO/system/pipeline/pick_topics.py" --date "$DATE"
  ;;

check)
  DIR="${1:-}"; [ -n "$DIR" ] || die "check 需要文章目录" 2
  if python3 "$REPO/system/pipeline/review_trace.py" "$DIR"; then
    audit "gate=pass cmd=check dir=$DIR"
  else
    audit "gate=fail cmd=check dir=$DIR"
    die "门禁不通过：该文未走完七刀（三件套不全），不予放行" 3
  fi
  ;;

ship)
  DIR="${1:-}"; shift || true
  [ -n "$DIR" ] && [ -d "$DIR" ] || die "ship 需要一个已存在的文章目录" 2
  DIR="$(cd "$DIR" && pwd)"
  DATE="$(date +%F)"; SLUG=""; DRY=0; PUSH=1; BYPASS=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --date) DATE="$2"; shift 2 ;;
      --slug) SLUG="$2"; shift 2 ;;
      --dry-run) DRY=1; shift ;;
      --no-push) PUSH=0; shift ;;
      --force-no-trace)
        BYPASS="${2:-}"
        [ -n "$BYPASS" ] && [ "${BYPASS#--}" = "$BYPASS" ] || die "--force-no-trace 必须带一句理由（会记入审计日志）" 2
        shift 2 ;;
      *) die "未知参数：$1" 2 ;;
    esac
  done
  [ -n "$SLUG" ] || SLUG="$(basename "$DIR")"

  # ── 第 1 步：门禁。唯一的绕过路径必须显式带理由，且照样落审计 ──────────────
  if [ -n "$BYPASS" ]; then
    echo "⚠ 门禁被显式跳过：$BYPASS"
    audit "gate=bypassed cmd=ship dir=$DIR reason=$BYPASS"
  elif python3 "$REPO/system/pipeline/review_trace.py" "$DIR"; then
    audit "gate=pass cmd=ship dir=$DIR"
  else
    audit "gate=fail cmd=ship dir=$DIR"
    die "门禁不通过：先补齐七刀三件套（01-brief / 03-arena / 06-review + final），或用 --force-no-trace \"理由\" 显式担责" 3
  fi

  # ── 第 2 步：转换桥 ────────────────────────────────────────────────────
  TO_POSTS=("python3" "$REPO/system/pipeline/to_posts.py" "$DIR" "--date" "$DATE" "--slug" "$SLUG")
  [ "$DRY" = 1 ] && TO_POSTS+=("--dry-run")
  "${TO_POSTS[@]}"
  OUT="$AIWRITER/posts/$DATE/$SLUG"

  # ── 第 3 步：提交到 AIWriter/main。走 detached worktree，不碰人的在途分支 ──
  # （L-014：跨仓库命令一律独立执行，本脚本全程 git -C，绝不在 RSI 仓库里 add/commit）
  if [ "$DRY" = 1 ]; then
    echo "[dry-run] 将执行："
    echo "  git -C $AIWRITER fetch origin main"
    echo "  git -C $AIWRITER worktree add --detach $WT origin/main"
    echo "  cp -R $OUT → $WT/posts/$DATE/$SLUG"
    echo "  git -C $WT add posts/$DATE/$SLUG && git -C $WT commit -m 'post($DATE): $SLUG'"
    [ "$PUSH" = 1 ] && echo "  git -C $WT push origin HEAD:main   # 触发配图+草稿箱同步 CI"
    echo "  git -C $AIWRITER worktree remove --force $WT"
    exit 0
  fi

  [ -f "$OUT/article.html" ] || die "转换未产出 $OUT/article.html"

  git -C "$AIWRITER" fetch origin main
  git -C "$AIWRITER" worktree remove --force "$WT" 2>/dev/null || true
  git -C "$AIWRITER" worktree add --detach "$WT" origin/main
  mkdir -p "$WT/posts/$DATE"
  cp -R "$OUT" "$WT/posts/$DATE/"
  git -C "$WT" add "posts/$DATE/$SLUG"
  git -C "$WT" commit -m "post($DATE): $SLUG"
  COMMIT="$(git -C "$WT" rev-parse --short HEAD)"
  if [ "$PUSH" = 1 ]; then
    git -C "$WT" push origin HEAD:main
    echo "✓ 已推送 AIWriter main commit=$COMMIT —— CI 将自动配图并同步草稿箱"
    echo "  下一步（会话手动）：gh run list -R <AIWriter repo> 取 run 号，拿到 media_id 后写 LEDGER 文章产出记录"
  else
    echo "✓ 已在 worktree 提交 commit=$COMMIT，未推送（--no-push）"
  fi
  audit "shipped dir=$DIR date=$DATE slug=$SLUG commit=$COMMIT push=$PUSH"
  git -C "$AIWRITER" worktree remove --force "$WT"
  ;;

*) die "未知子命令：$cmd（prep|check|ship）" 2 ;;
esac
