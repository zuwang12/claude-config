#!/usr/bin/env bash
# SessionStart 훅 — 같은 디렉터리에서 이전 세션이 남긴 상태를 컨텍스트에 주입한다.
# "이어서" 할 때 git log/status/WORKLOG를 각각 조회하는 것보다 싸다.
set -u

f="$HOME/.claude/session-state/$(pwd | tr '/' '-').txt"
[ -f "$f" ] || exit 0

python3 - "$f" <<'PY'
import io, json, sys
try:
    body = io.open(sys.argv[1], encoding="utf-8").read()
except Exception:
    sys.exit(0)
if not body.strip():
    sys.exit(0)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "[이 디렉터리에서 이전 세션이 남긴 상태]\n" + body,
    }
}, ensure_ascii=False))
PY

exit 0
