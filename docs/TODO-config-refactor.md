# config 구조 개편 — 다음 세션 작업 목록

작성: 2026-08-06 / 작성 세션: `[lgcns] CLAUDE.md 모델 선정 기준`

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

## 진행 상황 (2026-08-06 15:0x 갱신)

| 작업 | 상태 |
|---|---|
| 1. CLAUDE.md 분할 | **검증 대기.** 카나리아 배치 완료, 새 세션에서 확인 필요 (아래) |
| 2. `_inbox.md` | **완료.** 파일 생성 + CLAUDE.md에 「규칙 후보 수집함」 절·세션종료준비 4번 연결 |
| 3. SessionStart 훅 fetch | **완료.** 5개 케이스 테스트 통과 |
| 4. `install.sh` | **완료.** 5개 케이스 테스트 통과 |
| 5. `backup-before-rebase` 제거 | 미착수 (사용자 승인 대기) |

### 작업 1 검증 절차 (다음 세션에서 할 것)

`CLAUDE.md` 끝에 아래 3줄을, `rules/`에 카나리아 파일 2개를 넣어 두었다.
**내용은 아직 하나도 옮기지 않았으므로, import가 안 돼도 잃는 것이 없다.**

```
@rules/_import-test-rel.md              → CANARY-REL-8F3A  (상대경로)
@~/claude-config/rules/_import-test-abs.md → CANARY-ABS-2B7C  (절대경로 + 다중 import)
```

이 두 파일은 `~/.claude/CLAUDE.md` → `claude-config/CLAUDE.md` → `rules/*.md` 로
**2단계 중첩**이므로, 보이면 중첩·다중·경로형식 세 가지가 한 번에 검증된다.

1. **새 세션을 연다** (import는 세션 시작 때만 해석되므로 같은 세션에서는 확인 불가)
2. "카나리아 확인해 줘"라고 묻는다. 컨텍스트에 `CANARY-REL-8F3A`/`CANARY-ABS-2B7C`가
   있는지 본다. **파일을 Read해서 확인하면 안 된다** (그건 import 검증이 아니다)
3. 결과별 처리
   - **둘 다 보임** → 분할 진행 가능. 카나리아 3줄·파일 2개를 지우고 작업 1 착수
   - **하나만 보임** → 되는 경로 형식만 쓴다
   - **둘 다 안 보임** → **분할하지 않는다.** 카나리아를 지우고 작업 2·3·4만으로 마감

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

**미확인**: 회사 Windows 기계에 Git Bash가 있는지 확인되지 않았다. 없으면 `.sh` 훅이
안 돌고 PowerShell 버전이 따로 필요하다(`shell: "powershell"` 옵션 존재).
연구실 Ubuntu·도서관 Mac의 `jq`/python 버전도 미확인.

---

## 하지 말 것

- **작업 1을 import 검증 없이 시작하지 말 것.** 분할했는데 import가 안 되면
  4대 전부에서 규칙이 통째로 사라진다.
- **`~/.claude/`를 git으로 공유하려 하지 말 것.** 기계별 설정(경로·권한·MCP)이 섞여 있다.
  공유 대상은 `claude-config/` 아래뿐이다.
- **`cleanupPeriodDays`를 늘리지 말 것.** 트랜스크립트 30일 자동 정리는 정상 동작이다.
  이 기계는 백업이 없고 1.1GB가 이미 쌓여 있다.

## 현재 상태 (2026-08-06 15:0x)

- 훅 3종 등록·동작 확인 완료. `Stop`은 **동작 확인됨**(`session-state/` 파일이 13:19에 갱신됨).
  `PreCompact`는 여전히 미검증(compaction이 실제로 돌아야 확인 가능)
- `SessionStart` 훅에 fetch 추가. 오프라인일 때 **최대 5초** 세션 시작이 지연된다
  (`timeout 5`). 느린 환경에서 거슬리면 이 값을 줄인다
- `pull.rebase = true` (이 기계만. 다른 3대는 미설정)
- 세션 3개 아카이브 완료 (앱 목록 6개)
- 백업 ref `backup-before-rebase` 잔존. 문제 없으면 `git branch -D` 로 제거

### 다른 3대에 전파할 때

새 기계에서는 `bash ~/claude-config/install.sh` 한 줄이면 훅 등록이 끝난다
(`--dry-run` 으로 먼저 볼 수 있다). 여전히 미확인인 것:

- **회사 Windows**: Git Bash 유무. 없으면 `.sh` 훅이 안 돌고 PowerShell 버전이 필요하다
- **연구실 Ubuntu / 도서관 Mac**: python3 유무만 확인하면 된다(`jq`는 안 쓴다)
