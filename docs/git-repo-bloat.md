# `.git`이 비대할 때 — 원인 특정 절차

> 참고 문서. 상시 규칙이 아니라 **해당 증상이 났을 때 꺼내 보는 절차**라서
> `rules/` 가 아니라 여기에 둔다. (2026-08-08 승격 작업에서 `rules/` 편입은 기각)
>
> ⚠️ 2026-08-13 승격 작업에서 이 판단을 모르고 `rules/workflow.md` 에 다시 넣었다가
> 되돌렸다. 기각 기록이 push 되지 않아 다른 기계에서 보이지 않았던 것이 원인이다.
> **다시 올리지 말 것.** 이 절차가 자주 필요해지면 그때 스킬로 만든다.

## 관측 (2026-08-06, dell)

한 프로젝트 저장소의 `.git`이 1.2GB인데 정상 이력은 71MB뿐이었다. 원인은 **팩에 남은 도달 불가
객체 1개**(1.16GB zip)였다. `git add` 후 커밋이 취소되면 객체는 이미 기록된 뒤라,
이력에 보이지 않으면서 디스크는 계속 차지한다. `git log`·`git status`로는 전혀 안 보인다.

## 절차

1. `git count-objects -vH` → `size-pack`이 실제 사용량. `in-pack` 개수도 함께 본다.
2. 팩 내 최대 객체를 찾는다.
   ```bash
   git verify-pack -v .git/objects/pack/*.idx | grep -E '^[0-9a-f]{40}' | sort -k3 -rn | head
   ```
3. `git rev-list --objects --all | grep <sha>` → 출력이 없으면 **고아**(도달 불가).
4. 정상 이력 크기를 합산한다.
   ```bash
   git rev-list --objects --all | git cat-file --batch-check='%(objectsize:disk)' | awk '{s+=$1} END {print s}'
   ```
5. 1번과 4번의 차이가 곧 고아 용량이다. 제거는
   `git reflog expire --expire=now --all && git gc --prune=now`.

## ⚠️ 삭제 전에

**고아 객체가 이 기계의 유일본일 수 있다.** 삭제 전에 내용을 식별하고
(zip이면 중앙 디렉터리만 파싱해 파일 목록을 확인), 원본이 디스크 어딘가에 있는지 찾는다.
2026-08-06 건은 개인 자료였고 원본 폴더가 이미 삭제돼 **팩이 유일본**이었다.
