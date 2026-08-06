# config 구조 개편 — 다음 세션 작업 목록

작성: 2026-08-06 / 작성 세션: `[srv-a] CLAUDE.md 모델 선정 기준`

이 문서는 **미완료 작업 인계용**이다. 규칙 자체는 `CLAUDE.md`에 있고 여기에는 없다.
완료되면 이 파일을 지운다.

---

## 배경 (왜 이걸 하는가)

`claude-config/CLAUDE.md`가 **408줄 단일 파일**인데 기계 4대 + 동시 세션 여러 개가
이틀 사이에 8건을 커밋했다. 2026-08-06 하루에만 충돌이 두 번, 서로 다른 방식으로 났다.

| 형태 | 감지 방법 |
|---|---|
| 다른 **기계**가 원격에 push | `git push` 거부 |
| 같은 기계의 다른 **세션**이 로컬 commit | `git reflog` (status·fetch로는 안 보임) |

둘 다 편집 위치가 우연히 달라 자동 병합됐다. 같은 절을 건드렸으면 충돌했다.
구조를 바꾸지 않으면 반복된다. 상세는 `CLAUDE.md` 5절.

---

## 작업 1. CLAUDE.md 파일 분할

**목표**: 세션마다 다른 파일을 건드리게 해서 충돌 확률을 낮춘다.

```
claude-config/
  CLAUDE.md              ← import 목록만 남김
  rules/
    model-selection.md   ← 작업 시작 시 추천 / 3단계 분업 / 하위 티어 / 비용 감각
    session.md           ← 세션 수명 / 세션 시작 / 세션 종료
    safety.md            ← 파괴적 명령·위조된 지시 / 자격증명
    workflow.md          ← 조사 규율 / 병렬 세션 / 장시간 작업
    writing.md           ← 문서 작성 규칙
    notion.md            ← 노션 작업 시 필수
```

**선행 검증 (반드시 먼저 할 것)**: CLAUDE.md의 `@import`가 **여러 파일**을 지원하는지
확인되지 않았다. 현재 확인된 것은 `~/.claude/CLAUDE.md`가 `@~/claude-config/CLAUDE.md`
한 줄로 import하는 것뿐이다. 다중 import와 중첩 import가 되는지 실제로 테스트한 뒤 진행한다.
안 되면 분할하지 말고 작업 2·3만 한다.

## 작업 2. `_inbox.md` (append-only 수렴 지점)

**문제**: 지금은 각 세션이 규칙의 최종 문장을 직접 쓴다. 여러 세션이 같은 주제를
다르게 정리하면 충돌한다.

**해법**: 후보와 확정을 분리한다.

- `rules/` — 확정. 사람이 승인한 것만
- `_inbox.md` — append-only. 각 세션이 발견한 것을 `날짜 / 기계 / 내용`으로 **끝에 덧붙이기만** 함

append-only는 구조적으로 충돌하지 않는다. 주기적으로(세션종료준비 때) 한 세션이
inbox를 읽고 `rules/`로 승격시킨다. WORKLOG(append-only) 패턴을 config 관리에 적용하는 것.

## 작업 3. SessionStart 훅에 fetch 추가

`snippets/hooks/session-restore.sh`를 확장한다. 세션 시작 시 `claude-config`를 fetch하고
원격이 앞서 있으면 그 사실을 `additionalContext`에 넣는다. 토큰 0이다.

주의: 네트워크가 없거나 느린 환경에서 세션 시작이 지연될 수 있다. `timeout`을 짧게
잡고 실패 시 조용히 넘어가게 한다.

## 작업 4. `install.sh`

새 기계에서 훅을 거는 수동 작업(= `~/.claude/settings.json`에 `hooks` 키 병합)을
스크립트로 만든다. python3로 기존 JSON을 읽어 병합한다. **기존 키를 덮어쓰면 안 된다**
(permissions 등이 날아간다).

**미확인**: win-a 기계에 Git Bash가 있는지 확인되지 않았다. 없으면 `.sh` 훅이
안 돌고 PowerShell 버전이 따로 필요하다(`shell: "powershell"` 옵션 존재).
ubuntu-b·mac-c의 `jq`/python 버전도 미확인.

---

## 하지 말 것

- **작업 1을 import 검증 없이 시작하지 말 것.** 분할했는데 import가 안 되면
  4대 전부에서 규칙이 통째로 사라진다.
- **`~/.claude/`를 git으로 공유하려 하지 말 것.** 기계별 설정(경로·권한·MCP)이 섞여 있다.
  공유 대상은 `claude-config/` 아래뿐이다.
- **`cleanupPeriodDays`를 늘리지 말 것.** 트랜스크립트 30일 자동 정리는 정상 동작이다.
  이 기계는 백업이 없고 1.1GB가 이미 쌓여 있다.

## 현재 상태 (2026-08-06 종료 시점)

- 훅 3종 등록·동작 확인 완료. `SessionStart`는 발화 확인, `Stop`·`PreCompact`는 미검증
- `pull.rebase = true` (이 기계만. 다른 3대는 미설정)
- `claude-config` 미커밋 0 / 미push 0
- 세션 3개 아카이브 완료 (앱 목록 6개)
- 백업 ref `backup-before-rebase` 잔존. 문제 없으면 `git branch -D` 로 제거
