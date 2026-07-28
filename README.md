# claude-config

4개 환경에서 동일한 Claude Code 전역 지침을 쓰기 위한 리포.

| 환경 | OS | 위치 |
|---|---|---|
| 회사 | Windows | 로컬 |
| ubuntu-b | Ubuntu | 서버 |
| mac-c | macOS | 로컬 |
| srv-a | Ubuntu | LG CNS |

## 설계 원칙

**변하는 것과 안 변하는 것을 분리한다.**

| | 어디에 | 최신 유지 방법 |
|---|---|---|
| 모델 ID·가격·컨텍스트·effort 권장·fast 지원 | `claude-api` 스킬 | **자동** — Claude Code에 번들되어 앱과 함께 갱신 |
| 판단 절차·작업 프로토콜·조사 규율 | 이 리포 (`CLAUDE.md`) | `git pull` |
| auto memory·인증·`settings.local.json` | 각 기계 | 동기화하지 않음 (설계상 machine-local) |

`CLAUDE.md`에 모델 표를 **넣지 않는다.** 정적 표는 낡는다 — 실제로 이전 버전의
"Fable은 장문 컨텍스트가 강점" 근거가 낡아 있었다(Opus와 컨텍스트가 동일해짐).
대신 `CLAUDE.md`는 스킬을 *호출하는 규칙*만 담고, 값은 매번 스킬에서 읽는다.

## 설치 (4대 공통)

심볼릭 링크는 Windows에서 관리자 권한이나 개발자 모드가 필요하다.
**import 방식은 OS를 안 가리므로 4대 모두 같은 절차를 쓴다.**

```bash
git clone <이 리포 URL> ~/claude-config
mkdir -p ~/.claude
printf '@~/claude-config/CLAUDE.md\n' > ~/.claude/CLAUDE.md
```

Windows PowerShell:

```powershell
git clone <이 리포 URL> $HOME\claude-config
New-Item -ItemType Directory -Force $HOME\.claude | Out-Null
Set-Content -Path $HOME\.claude\CLAUDE.md -Value '@~/claude-config/CLAUDE.md' -NoNewline
```

### 설치 확인

세션을 열고 `/context`를 실행해 **Memory files**에 `CLAUDE.md`가 뜨는지 본다.
안 뜨면 `/memory`로 `~/.claude/CLAUDE.md`를 열어 경로를 확인한다.

`claude-api` 스킬이 그 기계에 있는지도 확인한다 — 세션에서 스킬 목록에 `claude-api`가
보이면 된다. 없으면 `CLAUDE.md`의 규칙이 "추천 생략"으로 안전하게 빠지도록 되어 있다.

## 갱신

```bash
git -C ~/claude-config pull
```

다음 세션부터 반영된다. 자동화하려면 `SessionStart` 훅으로 `git pull`을 걸 수 있으나,
**srv-a(LG CNS)처럼 외부 git 접근이 막힌 환경에서는 세션 시작이 지연되거나 실패할 수 있다.**
4대 중 한 곳이라도 GitHub 접근이 막히면 수동 `pull`을 권한다.

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
