# claude-config

4개 환경에서 동일한 Claude Code 전역 지침을 쓰기 위한 리포.

| 환경 | OS | 위치 |
|---|---|---|
| 회사 | Windows | 로컬 |
| ubuntu-b | Ubuntu | 서버 |
| mac-c | macOS | 로컬 |
| srv-a | Ubuntu | 사내망 |

## 설계 원칙

**변하는 것과 안 변하는 것을 분리한다.**

| | 어디에 | 최신 유지 방법 |
|---|---|---|
| 모델 ID·가격·컨텍스트·effort 권장·fast 지원 | `claude-api` 스킬 | **자동** — Claude Code에 번들되어 앱과 함께 갱신 |
| 판단 절차·작업 프로토콜·조사 규율 | 이 리포 (`CLAUDE.md`) | `git pull` |
| 노션 적재 방법론 | `notion-sync` 스킬 (이 리포) | `git pull` 또는 curl 재실행 |
| 노션 페이지 id·프로젝트 경로 | 프로젝트의 `notion_pages.json` | 동기화하지 않음 (프로젝트 로컬) |
| auto memory·인증·`settings.local.json` | 각 기계 | 동기화하지 않음 (설계상 machine-local) |

`CLAUDE.md`에 모델 표를 **넣지 않는다.** 정적 표는 낡는다 — 실제로 이전 버전의
"Fable은 장문 컨텍스트가 강점" 근거가 낡아 있었다(Opus와 컨텍스트가 동일해짐).
대신 `CLAUDE.md`는 스킬을 *호출하는 규칙*만 담고, 값은 매번 스킬에서 읽는다.

## 설치 (4대 공통)

public 리포이므로 **인증이 필요 없다.** 토큰도 `gh`도 SSH 키도 쓰지 않는다.

### 1단계 — 파일 받기

```bash
mkdir -p ~/claude-config
curl -fsSL https://raw.githubusercontent.com/zuwang12/claude-config/main/CLAUDE.md \
  -o ~/claude-config/CLAUDE.md
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\claude-config | Out-Null
Invoke-WebRequest -Uri https://raw.githubusercontent.com/zuwang12/claude-config/main/CLAUDE.md `
  -OutFile $HOME\claude-config\CLAUDE.md
```

`git`이 있으면 `git clone https://github.com/zuwang12/claude-config.git ~/claude-config` 도 된다.
갱신 이력을 보고 싶을 때만 git을 쓰고, 평소엔 curl 한 줄이 간단하다.

### 2단계 — import 한 줄 추가

**리다이렉션(`>`)으로 덮어쓰지 말 것.** 그 기계에 기존 `~/.claude/CLAUDE.md`가 있으면 날아간다.
에디터로 열어서 아래 한 줄을 **추가**한다.

```
@~/claude-config/CLAUDE.md
```

방법 세 가지. 편한 것을 쓴다.

**① Claude에게 시키기 (가장 간단).** 그 기계의 세션에서:

> `~/.claude/CLAUDE.md` 열어서 `@~/claude-config/CLAUDE.md` 한 줄 추가해줘 (기존 내용은 그대로 두고)

**② 셸 한 줄.** `>>`(추가)라 덮어쓰지 않고, 이미 있으면 중복 추가도 안 한다:

```bash
mkdir -p ~/.claude && grep -qxF '@~/claude-config/CLAUDE.md' ~/.claude/CLAUDE.md 2>/dev/null || printf '\n@~/claude-config/CLAUDE.md\n' >> ~/.claude/CLAUDE.md
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force $HOME\.claude | Out-Null; if (-not (Select-String -Path $HOME\.claude\CLAUDE.md -Pattern '^@~/claude-config/CLAUDE\.md$' -Quiet -ErrorAction SilentlyContinue)) { Add-Content $HOME\.claude\CLAUDE.md "`n@~/claude-config/CLAUDE.md" }
```

**③ 에디터로 직접.** `nano ~/.claude/CLAUDE.md` 등.

> `/memory` 는 터미널 CLI 전용이다. **데스크톱 앱에는 없다.**

파일이 없으면 이 줄만, 있으면 기존 내용은 두고 맨 위나 맨 아래에 덧붙인다.
위치는 로드 순서만 정한다(먼저 읽히길 원하면 위).

### 2-5단계 — 스킬·도구 받기 (노션 작업을 하는 기계만)

`CLAUDE.md`는 노션 규칙의 **트리거만** 담는다. 본문은 스킬로 분리해 뒀다 —
노션과 무관한 세션에서 토큰을 태우지 않기 위해서다(`claude-api`를 다룬 방식과 같다).

```bash
mkdir -p ~/.claude/skills/notion-sync
curl -fsSL https://raw.githubusercontent.com/zuwang12/claude-config/main/skills/notion-sync/SKILL.md \
  -o ~/.claude/skills/notion-sync/SKILL.md
```

clone 해 둔 기계라면 심볼릭 링크가 낫다 — `git pull` 하면 즉시 반영된다:

```bash
mkdir -p ~/.claude/skills && ln -sfn ~/claude-config/skills/notion-sync ~/.claude/skills/notion-sync
```

도구(`tools/notion_page.py`)는 clone 한 기계면 이미 있다. curl로 받은 기계는 필요할 때 받는다.

**페이지 id는 이 리포에 넣지 않는다.** 프로젝트 디렉터리에 `notion_pages.json`을 두고
스크립트가 그걸 읽는다(`.gitignore`에 등록돼 있다).

### 3단계 — 확인

새 세션에서 `/context` → **Memory files**의 토큰 수를 본다.

| 값 | 판정 |
|---|---|
| ~4k | ✅ import 성공 |
| ~10 미만 | ❌ 실패 — `@` 뒤를 절대경로로 교체 (`@/home/<사용자명>/claude-config/CLAUDE.md`) |

또는 세션에서 물어본다: **"내 CLAUDE.md에 모델·노력·속도 추천 규칙 있어?"**
트리거 조건을 답하면 성공이다.

### 설치 확인

세션을 열고 `/context`를 실행해 **Memory files**에 `CLAUDE.md`가 뜨는지 본다.
안 뜨면 `~/.claude/CLAUDE.md`를 직접 열어 `@` 줄의 경로를 확인한다.

`claude-api` 스킬이 그 기계에 있는지도 확인한다 — 세션에서 스킬 목록에 `claude-api`가
보이면 된다. 없으면 `CLAUDE.md`의 규칙이 "추천 생략"으로 안전하게 빠지도록 되어 있다.

## 갱신

**설치 1단계의 curl을 그대로 다시 실행하면 된다.** 덮어쓰기가 곧 갱신이다.

```bash
curl -fsSL https://raw.githubusercontent.com/zuwang12/claude-config/main/CLAUDE.md \
  -o ~/claude-config/CLAUDE.md
```

clone 해 둔 기계라면 `git -C ~/claude-config pull` 도 같다.
(`git -C <경로>`는 그 디렉토리로 `cd` 한 것처럼 실행하되 현재 위치는 바꾸지 않는다.)

다음 세션부터 반영된다. 자동화하려면 `SessionStart` 훅에 걸 수 있으나,
**사내망 서버처럼 외부 접근이 막힌 환경에서는 세션 시작이 지연되거나 실패할 수 있다.**
4대 중 한 곳이라도 GitHub 접근이 막히면 수동 갱신을 권한다.
raw.githubusercontent.com 도 막혀 있으면 파일 하나뿐이니 복사해 붙여넣어도 된다.

## 수정할 때

원본은 항상 `~/claude-config/CLAUDE.md`다. `~/.claude/CLAUDE.md`는 한 줄짜리 stub이므로
거기를 고치면 안 된다(다음 `pull`에서 덮이지는 않지만 다른 기계에 반영되지 않는다).

```bash
$EDITOR ~/claude-config/CLAUDE.md
git -C ~/claude-config commit -am "..." && git -C ~/claude-config push
```

`CLAUDE.md`는 **200줄 이하**로 유지한다. 길어지면 준수율이 떨어진다.
주제별로 쪼갤 거면 `~/.claude/rules/`(사용자 스코프, 모든 프로젝트에 적용)를 쓰되,
import든 rules든 **시작 시 전부 컨텍스트에 로드되므로 토큰은 절약되지 않는다.**

## 동기화하지 않는 것

- **auto memory** (`~/.claude/projects/<project>/memory/`) — 문서상 machine-local이며
  기계 간 공유되지 않는다. 기계별로 따로 쌓인다.
- **`settings.local.json`, 인증 토큰, 세션 기록** — 기계·계정에 묶인다.
- 프로젝트별 `CLAUDE.md` — 해당 프로젝트 리포에 커밋한다(예: `mail-system`).
