#!/usr/bin/env bash
# SessionStart 훅 — 세션 시작 시 두 가지를 컨텍스트에 주입한다. 토큰 비용 0.
#   1. 같은 디렉터리에서 이전 세션이 남긴 상태 (Stop 훅이 쌓아 둔 것)
#   2. 공유 config 저장소가 원격·로컬과 갈라졌는지 (fetch 포함)
# "이어서" 할 때 git log/status/fetch를 각각 조회하는 것보다 싸다.
set -u

CTX=""

# --- 1. 이전 세션 상태 --------------------------------------------------
f="$HOME/.claude/session-state/$(pwd | tr '/' '-').txt"
if [ -s "$f" ]; then
  CTX="[이 디렉터리에서 이전 세션이 남긴 상태]
$(cat "$f" 2>/dev/null)"
fi

# --- 2. claude-config 이탈 여부 ----------------------------------------
# 네트워크가 없거나 느린 환경에서 세션 시작을 붙잡지 않도록 timeout 을 짧게 잡고,
# 실패하면 조용히 넘어간다(마지막으로 알려진 ref 로 계산이 이어진다).
CFG="$HOME/claude-config"
if [ -d "$CFG/.git" ]; then
  GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -oBatchMode=yes' \
    timeout 5 git -C "$CFG" fetch -q 2>/dev/null

  counts=$(git -C "$CFG" rev-list --left-right --count HEAD...@{u} 2>/dev/null || true)
  ahead=$(printf '%s' "$counts" | awk '{print $1+0}')
  behind=$(printf '%s' "$counts" | awk '{print $2+0}')
  dirty=$(git -C "$CFG" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

  note=""
  if [ "${behind:-0}" -gt 0 ] 2>/dev/null; then
    note="$note
- 원격이 $behind 커밋 앞서 있다. **편집 전에 pull 할 것** (다른 기계가 push함)."
  fi
  if [ "${ahead:-0}" -gt 0 ] 2>/dev/null; then
    note="$note
- 로컬이 $ahead 커밋 앞서 있다(미push)."
  fi
  if [ "${dirty:-0}" -gt 0 ] 2>/dev/null; then
    note="$note
- 미커밋 $dirty 건."
  fi

  if [ -n "$note" ]; then
    [ -n "$CTX" ] && CTX="$CTX
"
    CTX="$CTX[claude-config 상태]$note"
  fi
fi

[ -n "$CTX" ] || exit 0

CTX="$CTX" python3 - <<'PY'
import json, os
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": os.environ["CTX"],
    }
}, ensure_ascii=False))
PY

exit 0
