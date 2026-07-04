# llmw

[English](README.md) · **한국어** · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · [Français](README.fr.md)

AI 에이전트를 위한 헤드리스 Obsidian 스타일의 LLM Wiki CLI.

## 왜 필요한가

MCP 도구는 편리하지만, 도구 스키마와 긴 명령문은 매 턴마다 컨텍스트를 소비합니다. `llmw`는 다른 접근법을 취합니다: 작은 결정론적 CLI와 Claude Code 스킬 조합입니다. 에이전트는 필요할 때만 위키를 호출하고, CLI 자체는 절대 모델을 호출하지 않습니다. 인덱싱, 검색, 검증만 수행합니다.

## 개념

- **Karpathy LLM Wiki** — `raw/`는 불변의 소스 자료를 보유하고, `wiki/`는 AI 에이전트가 작성하고 유지보수하는 영구 지식층입니다. 이는 일반적인 RAG가 아닌, 위키는 복합적으로 누적되는 산출물입니다.
- **Obsidian 스타일 위키링크** — `[[Page]]`, `[[Page|Alias]]`, `[[Page#Heading]]`, `![[Embed]]`, 백링크, 태그, YAML 프론트매터. `wiki/`는 유효한 Obsidian 볼트입니다. 원하면 그곳에서 열어 같은 파일 위에 인간 친화적인 시각적 IDE를 사용할 수 있습니다.
- **Markdown을 진실의 원천으로** — `.llmw/index.sqlite`와 `.llmw/graph.json`은 파생되고 재구성 가능한 데이터입니다. `llmw rebuild`는 `wiki/*.md`만으로 둘 다 재생성합니다.
- **AI 에이전트가 위키를 작성하고, CLI가 인덱싱하고 검증합니다** — 검색(SQLite FTS5), 백링크, 관련 페이지 점수 매기기, 린트는 모두 결정론적이고 규칙 기반이며 모델 없는 작업입니다. 소스 요약, 페이지 작성, 보관할 항목 결정은 에이전트의 일입니다.

## 설치

**권장: Claude Code 플러그인** — 별도의 `pip`/`uv`/`pipx` 단계 없음:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

이것은 또한 CLI 자체를 자동으로 동기화 상태로 유지하고 에이전트가 그것을 우회하는 것을 방지하는 훅을 설치합니다 — [docs/ko/hooks.md](docs/ko/hooks.md)를 참조하세요.

스탠드얼론 CLI를 직접 원하시나요(스크립팅, CI, 다른 에디터), 또는 업그레이드를 직접 관리하시겠어요? 
[docs/ko/installation.md](docs/ko/installation.md)를 참조하세요(Windows/macOS/Linux별 완전한 uv/pipx/pip/dev 설치 매트릭스). 둘은 충돌하지 않습니다 — 둘 다 설치할 수 있습니다.

## 빠른 시작

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init`은 다음을 구성합니다:

```text
raw/                          # 불변의 소스 자료
wiki/                         # 에이전트가 유지보수하는 지식층
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 파생 인덱스/캐시/백업/잠금(재구성 가능)
.claude/skills/llm-wiki/      # SKILL.md + reference.md + examples.md
.claude-plugin/plugin.json    # 이 프로젝트를 위한 선택적 플러그인 메타데이터
```

`--layout ai-wiki`를 전달하여 `raw/`/`wiki/`/`.llmw/`를 `ai-wiki/` 폴더 아래에 중첩하고(이후의 모든 명령에서 자동 감지됨), `--adopt`를 전달하여 기본 콘텐츠를 구성하지 않고 이미 자체 규칙에 따라 실제 콘텐츠가 있는 위키를 가리킵니다 — [docs/ko/project-layout.md](docs/ko/project-layout.md)를 참조하세요.

## 에이전트 워크플로우

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## 명령 참조

모든 명령은 기계 해석 가능한 출력을 위해 `--json`을 수용합니다. 대부분의 읽기는 간단하고 컨텍스트가 저렴한 보기를 기본값으로 합니다(`--full`/`--no-brief`로 더 보기).

| 명령 | 목적 |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | `raw/`, `wiki/`, `.llmw/`를 구성합니다(ai-wiki/` 아래 중첩됨 `--layout ai-wiki` 포함). `--adopt`는 기본 콘텐츠/분류 구성을 건너뛰고 기존 위키 콘텐츠와 구성 재정의를 보호합니다 |
| `llmw status [--brief\|--json]` | 페이지 수, 끊긴 링크, 고아 페이지, 마지막 인덱싱 시간, 더티 페이지 |
| `llmw rebuild` | `wiki/**/*.md`의 전체 재인덱싱 |
| `llmw index [--changed\|--all]` | 증분(기본값) 또는 전체 재인덱싱 |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | 제목/요약/본문에 대한 SQLite FTS5 검색 — 검색 의미론은 [docs/ko/commands.md](docs/ko/commands.md)를 참조 |
| `llmw read <path\|title\|alias> [--full\|--brief]` | 페이지 조회; brief는 제목/유형/요약/핵심 포인트/링크/백링크 수 표시 |
| `llmw links <target>` | 나가는 링크, 끊김 상태 포함 |
| `llmw backlinks <target>` | 들어오는 링크 |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 결정론적 관련 페이지 후보(모델 호출 없음) |
| `llmw ingest <raw/...>` | `.md`/`.txt` 소스를 `wiki/sources/<slug>.md` 초안으로 등록 |
| `llmw write <path> --reason "..." --stdin [--force]` | stdin에서 새 위키 페이지 작성 |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 기존 페이지에서 정확한 문자열 바꾸기(네이티브 Edit 도구와 동일한 의미론) |
| `llmw patch <path> --reason "..." --stdin` | 기존 페이지에 통합 diff 적용(먼저 백업, 실패 시 롤백) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | 페이지를 `wiki/archived/YYYY/MM/`로 이동, 아카이브 프론트매터 스탬프, 변경 기록 |
| `llmw lint [--brief\|--json]` | 끊긴 링크, 고아 페이지, 중복 제목/별칭, 누락/잘못된 프론트매터, 매달린 raw 참조, 아카이브된 페이지 링크 — 보고만 하고 자동 수정 없음 |
| `llmw health [--brief]` | 시스템 검사: 구성, 인덱스 db, 스키마 버전, 디렉토리, 잠금 |
| `llmw graph build` / `llmw graph export --format json\|html` | 링크 그래프 재생성/내보내기 |

## 안전 규칙

- `raw/`는 불변입니다. `write`/`patch`/`archive`는 그 아래의 모든 경로를 거부합니다.
- 모든 `write`/`patch`/`archive`는 `--reason`이 필요하고, `wiki/log.md`와 `log_entries` 테이블에 기록됩니다.
- `delete`는 없습니다. `archive`를 사용하세요. 기본값은 원래 위치에서 새 위치를 가리키는 묘비 스텁을 유지합니다.
- `patch`는 diff를 적용하기 전에 파일을 백업하고, diff가 깔끔하게 적용되지 않으면(컨텍스트 불일치) 원본을 건드리지 않은 상태로 둡니다.
- 간단한 권고 잠금(`.llmw/locks/write.lock`)이 두 개의 `llmw` 프로세스가 동시에 위키를 변경하는 것을 방지합니다.

## 문서

| 문서 | 설명 |
|---|---|
| [docs/ko/installation.md](docs/ko/installation.md) | 완전한 스탠드얼론 CLI 설치 매트릭스(Windows/macOS/Linux), 업그레이드, 제거 |
| [docs/ko/hooks.md](docs/ko/hooks.md) | Claude Code 플러그인의 `PreToolUse` 위키 가드 및 자동 치유 `SessionStart` 버전 동기화 훅 |
| [docs/ko/commands.md](docs/ko/commands.md) | 검색 의미론(3단계 폴백, 한국어 입자 어간 제거) |
| [docs/ko/project-layout.md](docs/ko/project-layout.md) | 클래식 vs `ai-wiki/` 레이아웃, `--root`/`LLMW_ROOT`, `--adopt`, 기존 위키의 규칙에 llmw 적응, Obsidian 호환성 참고 |
| [docs/ko/development.md](docs/ko/development.md) | 개발 설정, Claude Code 스킬, MVP 범위 |

## 라이선스

MIT — [LICENSE](LICENSE) 참조.
