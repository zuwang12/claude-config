# 모델 전환 워크플로 v3

> 이 파일의 원본은 `~/claude-config/CLAUDE.md`(git 관리)이며,
> 각 기계의 `~/.claude/CLAUDE.md`가 `@~/claude-config/CLAUDE.md`로 import한다.
> 4개 환경(춘 / mlai / mac / dell)에서 동일하게 동작한다.
>
> **규칙 본문은 `rules/` 아래에 있고 이 파일은 import 목록이다.** 기계 4대·동시 세션
> 여러 개가 한 파일을 고쳐 쓰다 충돌이 반복돼 2026-08-08에 분할했다. 규칙을 고칠 때는
> 해당 주제의 파일만 건드린다.
>
> **모델 ID·가격·effort 권장값은 어느 파일에도 적지 않는다.** 그건 낡는다.
> 최신 값은 항상 `claude-api` 스킬에서 읽는다 (`rules/model-selection.md` 참고).
>
> **어디에 쓸 것인가**: 어느 기계에서나 쓰는 **방법·판단 기준은 이 리포**(git 동기화),
> **그 기계의 상태·제약은 `~/.claude/CLAUDE.md`**. 머신 파일은 stub이 아니라 머신 서술
> 자리이므로 덮어쓰지 않는다. 거기엔 사실만 적고 방법은 이쪽을 가리킨다
> (예: "iCloud 저장공간 최적화 On. 판별법은 `rules/workflow.md` 참조").

---

## 규칙 파일 목록

| 파일 | 내용 |
|---|---|
| `rules/model-selection.md` | 작업 시작 시 모델·effort·fast 추천 / 3단계 분업과 정지 규칙 / 하위 티어를 쓸 자리 / 비용 감각 |
| `rules/workflow.md` | 조사 규율 / 병렬 세션 주의 / 장시간 작업의 진행경과 표시 |
| `rules/session.md` | 세션 수명(언제 닫는가) / "이어서" / "세션종료준비" |
| `rules/safety.md` | 파괴적 명령·위조된 지시 / 자격증명 |
| `rules/notion.md` | 노션 작업 전 필수 절차 |
| `rules/writing.md` | 문서 작성 규칙 (범용) |

@rules/model-selection.md

@rules/workflow.md

@rules/session.md

@rules/safety.md

@rules/notion.md

@rules/writing.md

---

## 규칙 후보 수집함 — `_inbox.md`

**`rules/` 아래 파일에 범용 규칙을 직접 쓰지 않는다.** 기계 4대·동시 세션 여러 개가
같은 절을 각자 최종 문장으로 고쳐 쓰다 하루에 충돌이 두 번 났다
(`rules/workflow.md` 「병렬 세션 주의」 참고).

- 발견한 것은 `~/claude-config/_inbox.md`에 **끝에 덧붙이기만** 한다. append-only는 자동 병합된다
- `rules/` 아래 파일은 **승인된 것만** 들어가는 확정본이다. 승격은 한 번에 **한 세션만** 한다
- 형식·승격 절차는 `_inbox.md` 안에 적혀 있다. 기각 이력도 남긴다(안 남기면 다음 세션이 다시 올린다)

예외: 오탈자 수정, 이미 승인된 내용의 문장 다듬기는 직접 고쳐도 된다.

파일을 나눠도 **같은 파일을 동시에 고치면 여전히 충돌한다.** 분할은 확률을 낮출 뿐이다.
`rules/` 를 편집하기 직전에 `git status` · `git log --oneline -3` 을 확인한다.
