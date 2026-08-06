#!/usr/bin/env bash
# 새 기계에 claude-config 훅을 설치한다.
#
#   bash ~/claude-config/install.sh          # 설치
#   bash ~/claude-config/install.sh --dry-run # 무엇이 바뀌는지 보기만
#
# ~/.claude/ 는 기계별 로컬이라 git 으로 공유하지 않는다. 그래서 훅 '등록'만
# 이 스크립트가 대신한다. 훅 '본체'는 git 으로 내려온 snippets/hooks/*.sh 를 그대로 참조한다
# (심볼릭 링크를 만들지 않는다. git pull 하면 자동으로 최신이 된다).
#
# ⚠️ settings.json 의 기존 키(permissions 등)를 덮어쓰지 않는다. hooks 안에서도
#    다른 훅이 이미 등록돼 있으면 보존하고 우리 것만 추가한다.
set -eu

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

CFG_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$HOME/.claude/settings.json"

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 가 필요하다. (jq 는 없는 기계가 있어 python3 로 통일했다)" >&2
  exit 1
}

# 훅 본체가 실제로 있는지 먼저 확인한다. 없는 것을 등록하면 매 세션 조용히 실패한다.
for h in session-snapshot.sh precompact-warn.sh session-restore.sh; do
  [ -f "$CFG_DIR/snippets/hooks/$h" ] || { echo "ERROR: $CFG_DIR/snippets/hooks/$h 없음" >&2; exit 1; }
done
[ "$DRY" -eq 1 ] || chmod +x "$CFG_DIR/snippets/hooks/"*.sh

mkdir -p "$HOME/.claude"

DRY="$DRY" SETTINGS="$SETTINGS" python3 - <<'PY'
# -*- coding: utf-8 -*-
# python 3.8 호환으로 쓴다 (이 기계의 시스템 python 이 3.8.10).
from __future__ import print_function
import io, json, os, shutil, sys, time

settings = os.environ["SETTINGS"]
dry = os.environ["DRY"] == "1"

WANT = [
    ("Stop",         "session-snapshot.sh", {"timeout": 10, "async": True}),
    ("PreCompact",   "precompact-warn.sh",  {"timeout": 10}),
    ("SessionStart", "session-restore.sh",  {"timeout": 10}),
]

# 경로는 $HOME 을 그대로 둔다. 기계마다 홈 디렉터리가 달라도 같은 문자열이 쓰인다.
def cmd_for(script):
    return "$HOME/claude-config/snippets/hooks/" + script

data = {}
if os.path.exists(settings):
    try:
        with io.open(settings, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        print("ERROR: %s 가 올바른 JSON 이 아니다: %s" % (settings, e))
        print("       손으로 고친 뒤 다시 실행할 것. 아무것도 바꾸지 않았다.")
        sys.exit(1)
    if not isinstance(data, dict):
        print("ERROR: %s 최상위가 객체가 아니다. 중단." % settings)
        sys.exit(1)

hooks = data.get("hooks")
if hooks is None:
    hooks = {}
elif not isinstance(hooks, dict):
    print("ERROR: settings.json 의 hooks 가 객체가 아니다. 중단.")
    sys.exit(1)

added, kept = [], []
for event, script, opts in WANT:
    cmd = cmd_for(script)
    groups = hooks.get(event) or []
    if not isinstance(groups, list):
        print("ERROR: hooks.%s 가 배열이 아니다. 중단." % event)
        sys.exit(1)

    # 이미 같은 스크립트가 등록돼 있으면 건드리지 않는다 (재실행해도 중복되지 않는다).
    already = False
    for g in groups:
        for h in (g or {}).get("hooks", []) or []:
            if script in str((h or {}).get("command", "")):
                already = True
    if already:
        kept.append(event + " / " + script)
        continue

    entry = {"type": "command", "command": cmd}
    entry.update(opts)
    groups = list(groups) + [{"hooks": [entry]}]   # 남의 훅은 보존하고 뒤에 붙인다
    hooks[event] = groups
    added.append(event + " / " + script)

for line in kept:
    print("  유지  %s (이미 등록됨)" % line)
for line in added:
    print("  추가  %s" % line)

if not added:
    print("\n변경 없음. 이미 설치돼 있다.")
    sys.exit(0)

data["hooks"] = hooks
blob = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

if dry:
    print("\n--dry-run 이라 쓰지 않았다. 적용될 hooks:")
    print(json.dumps(hooks, ensure_ascii=False, indent=2))
    sys.exit(0)

if os.path.exists(settings):
    bak = settings + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(settings, bak)
    print("\n백업: %s" % bak)

tmp = settings + ".tmp"
with io.open(tmp, "w", encoding="utf-8") as f:
    f.write(blob)
os.rename(tmp, settings)      # 원자적 교체. 중간에 죽어도 반쪽 파일이 남지 않는다
print("기록: %s" % settings)
PY

echo
if [ "$DRY" -eq 1 ]; then
  echo "dry-run 종료."
else
  cat <<'EOS'
⚠️ 앱에서 세션을 재시작해야 반영된다(설정 감시자는 세션 시작 시점만 본다).
   확인: 새 세션을 열고 `~/.claude/session-state/` 에 파일이 생기는지 본다.

미확인 환경:
  - Windows: Git Bash 가 있어야 이 스크립트와 .sh 훅이 돈다. 없으면
    settings.json 의 hook 에 "shell": "powershell" 을 쓰는 별도 버전이 필요하다.
  - macOS: 기본 bash 가 3.2 라도 이 스크립트는 동작한다(python3 만 있으면 된다).
EOS
fi
