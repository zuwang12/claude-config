#!/usr/bin/env bash
# Stop 훅 — 턴이 끝날 때마다 현재 작업 디렉터리의 git 상태를 스냅샷으로 남긴다.
# 셸에서만 돌고 모델을 호출하지 않으므로 토큰 비용 0.
# 저장 위치: ~/.claude/session-state/<경로를 -로 치환>.txt
set -u

STATE_DIR="$HOME/.claude/session-state"
mkdir -p "$STATE_DIR" 2>/dev/null || exit 0

d=$(pwd)
# git 저장소가 아니면 남길 것이 없다
git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || exit 0

s=$(printf '%s' "$d" | tr '/' '-')
{
  echo "# cwd: $d"
  echo "# saved: $(date '+%F %T')"
  echo "# branch: $(git -C "$d" branch --show-current 2>/dev/null)"
  echo "# unpushed: $(git -C "$d" log --oneline '@{u}..' 2>/dev/null | wc -l | tr -d ' ')"
  echo "# uncommitted:"
  git -C "$d" status --porcelain 2>/dev/null | head -40
} > "$STATE_DIR/$s.txt" 2>/dev/null

exit 0
