#!/usr/bin/env bash
# PreCompact 훅 — compaction 직전은 "컨텍스트가 찼다"는 신호다.
# 세션 수명 규칙(~/claude-config/CLAUDE.md)의 교체 시점 중 하나이므로 사용자에게 알린다.
# 토큰 비용 0.
set -u

n="-"
if git rev-parse --git-dir >/dev/null 2>&1; then
  n=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
fi

python3 - "$n" <<'PY'
import json, sys
n = sys.argv[1]
msg = (
    "컨텍스트가 찼습니다 (compaction 실행됨). 세션 교체를 검토할 시점입니다.\n"
    "  미커밋 %s개. 이어서 작업하면 다음 턴부터 누적 이력이 재청구됩니다.\n"
    "  닫으려면 '세션종료준비' 라고 하세요." % n
)
print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
PY

exit 0
