# llmw

[English](README.md) · **한국어** · [日本語](README.ja.md) · [简体中文](README.zh-Hans.md) · [Español](README.es.md) · [Français](README.fr.md)

AI 코딩 어시스턴트에게 프로젝트 전용 개인 노트("위키")를 만들어 주는 간단한 커맨드라인 도구입니다. 덕분에 대화가 끝나도 그때그때 모든 걸 잊어버리는 대신, 그동안 내린 결정이나 알게 된 사실, 그리고 프로젝트의 역사를 계속 기억할 수 있습니다.

## 왜 쓰나요?

많은 AI 도구들은 메시지를 보낼 때마다 긴 지침과 데이터 덩어리를 통째로 밀어 넣는 방식으로 동작합니다. 이렇게 하면 공간도 낭비되고 속도도 느려지죠. `llmw`는 다릅니다. AI가 정말 뭔가를 찾아보거나 기록해야 할 때만 손을 뻗는, 작고 단순한 도구입니다. 이 도구 자체는 절대로 "생각"하거나 글을 지어내지 않습니다. 그저 메모를 저장하고, 나중에 다시 찾아주고, 제대로 작성됐는지 확인만 할 뿐입니다. 무엇을 적을지, 어떻게 요약할지 같은 실제 사고는 전부 AI가 합니다. `llmw`가 하는 게 아닙니다.

## 기본 아이디어

- **폴더 두 개, 역할 두 개** — `raw/`에는 절대 바뀌지 않는 원본 자료가 들어갑니다(업로드한 문서 같은 것들). `wiki/`는 AI가 직접 메모를 작성하는 곳으로, 알아가는 게 늘어날수록 계속 내용을 고쳐 씁니다. 그래서 이 노트는 한 번 검색하고 끝나는 게 아니라 시간이 지날수록 점점 더 쓸모 있어집니다.
- **서로 연결되는 메모** — 페이지는 다른 페이지를 링크로 연결할 수 있습니다(위키백과 링크처럼). 그래서 AI가 관련된 메모를 따라가며 살펴볼 수 있습니다. 이 방식은 인기 있는 노트 앱인 [Obsidian](https://obsidian.md/)에서도 그대로 동작하므로, 원한다면 같은 메모를 직접 눈으로 훑어볼 수도 있습니다.
- **전부 그냥 텍스트 파일** — 모든 메모는 평범한 Markdown 파일이라서 직접 열어서 읽을 수 있고, 특별한 데이터베이스도 필요 없습니다. 검색을 도와주는 작은 인덱스 파일이 하나 있긴 하지만, 이건 그냥 보조 도구일 뿐이라 필요하면 메모들로부터 언제든 다시 만들어낼 수 있습니다.
- **AI는 글을 쓰고, 도구는 확인하고 정리만** — 검색하기, 관련 메모 찾기, 메모가 제대로 작성됐는지 확인하기는 전부 단순하고 예측 가능한 작업이며 AI가 개입하지 않습니다. 무엇을 적어둘 가치가 있는지 판단하고 잘 쓰는 일은 AI의 몫입니다.

## 설치

**추천: Claude Code 플러그인으로 설치** — 명령어 딱 두 줄이면 끝, 따로 준비할 것도 없습니다:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

이렇게 하면 모든 게 알아서 잘 굴러가도록 도와주는 안전장치도 몇 가지 함께 설치됩니다. 자세한 내용은 [docs/ko/hooks.md](docs/ko/hooks.md)를 보세요.

Claude Code 밖에서도 쓰려고 커맨드라인 도구를 직접 설치하고 싶으신가요? [docs/ko/installation.md](docs/ko/installation.md)에 Windows, macOS, Linux별로 하나하나 따라 할 수 있는 설치 방법이 있습니다. 둘 다 설치해도 서로 방해되지 않으니 같이 설치하셔도 됩니다.

**Codex 플러그인**은 다음처럼 설치합니다(`uvx`가 포함된 [uv](https://docs.astral.sh/uv/)만 미리 필요합니다):

```text
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

별도의 CLI 설치 없이 `llmw_init`, `llmw_status`, `llmw_search`, `llmw_read`, `llmw_write`가 Codex 네이티브 도구로 등록됩니다. 플러그인은 고정된 GitHub 릴리스를 `uvx`로 실행합니다.

## 빠르게 시작하기

```bash
mkdir my-project && cd my-project
llmw init
llmw status --brief
```

`llmw init`을 실행하면 이런 폴더 구조가 만들어집니다:

```text
raw/                          # 원본 자료 — 절대 수정하지 않음
wiki/                         # AI가 계속 고쳐 쓰는 자기 메모
  index.md overview.md log.md
  sources/ entities/ concepts/ decisions/ syntheses/ projects/ glossary/ archived/
.llmw/                        # 뒤에서 돌아가는 검색 인덱스(언제든 다시 만들 수 있음)
.claude/skills/llm-wiki/      # Claude Code에게 이 도구 쓰는 법을 알려줌
.claude/rules/llm-wiki.md     # 작업 전 검색·후 업데이트를 자동으로 유도하는 규칙
.claude-plugin/plugin.json    # 이 프로젝트를 위한 선택적 플러그인 정보
```

프로젝트 폴더를 더 깔끔하게 유지하려고 이 모든 걸 하위 폴더 하나에 몰아넣고 싶으신가요? 아니면 이미 직접 만들어 둔 위키를 `llmw`가 그대로 쓰게 하고 싶으신가요? [docs/ko/project-layout.md](docs/ko/project-layout.md)를 확인해보세요.

## AI가 실제로 쓰는 방식

```bash
llmw status --brief
llmw search "previous decision" --limit 5
llmw read wiki/decisions/foo.md --brief
llmw patch wiki/decisions/foo.md --reason "updated after new test" --stdin
llmw lint --brief
```

## 전체 명령어

모든 명령어는 프로그램이 읽기 좋은 형식으로 결과를 받고 싶다면 `--json`을 지원합니다. 대부분의 "읽기" 명령어는 기본적으로 짧은 요약만 보여줍니다(전체 내용을 보려면 `--full`이나 `--no-brief`를 붙이세요).

| 명령어 | 하는 일 |
|---|---|
| `llmw init [--force] [--no-claude-plugin] [--layout classic\|ai-wiki] [--adopt]` | 새 프로젝트에 `raw/`, `wiki/`, 검색 인덱스를 만듭니다(이미 있는 프로젝트라면 `--adopt`를 붙이세요 — [docs/ko/project-layout.md](docs/ko/project-layout.md) 참고) |
| `llmw status [--brief\|--json]` | 빠른 상태 점검: 메모가 몇 개 있는지, 끊긴 링크가 있는지, 마지막으로 언제 갱신됐는지 |
| `llmw rebuild` | 검색 인덱스를 처음부터 전부 다시 만듭니다 |
| `llmw index [--changed\|--all]` | 검색 인덱스를 갱신합니다(기본은 바뀐 부분만) |
| `llmw search "<query>" [--limit N] [--type T] [--strict]` | 모든 메모를 검색합니다 — 검색이 어떻게 동작하는지는 [docs/ko/commands.md](docs/ko/commands.md) 참고 |
| `llmw read <path\|title\|alias> [--full\|--brief]` | 메모를 엽니다. 짧은 버전은 제목, 요약, 링크만 보여줍니다 |
| `llmw links <target>` | 이 메모가 어디로 링크하는지 보여줍니다 |
| `llmw backlinks <target>` | 다른 메모 중 어떤 것이 이 메모로 링크하는지 보여줍니다 |
| `llmw related <target> [--limit N] [--by links,tags,terms]` | 간단한 규칙으로 관련 메모를 추천합니다(AI의 추측은 개입하지 않음) |
| `llmw ingest <raw/...>` | 원본 문서를 AI가 채워 넣을 초안 메모로 바꿔줍니다 |
| `llmw write <path> --reason "..." --stdin [--force]` | 완전히 새로운 메모를 만듭니다 |
| `llmw edit <path> --old "..." --new "..." --reason "..." [--all]` | 기존 메모에서 정확히 일치하는 한 부분만 바꿉니다 |
| `llmw patch <path> --reason "..." --stdin` | 메모에 여러 변경 사항을 한꺼번에 적용합니다(먼저 백업하고, 문제가 생기면 스스로 되돌립니다) |
| `llmw archive <path> --reason "..." [--tombstone\|--no-tombstone]` | 오래된 메모를 지우는 대신 옆으로 치워두고, 새 위치를 알려주는 메모를 남겨둡니다 |
| `llmw lint [--brief\|--json]` | 끊긴 링크, 빠진 정보, 중복된 제목 같은 문제를 찾아줍니다(자동으로 고쳐주진 않습니다) |
| `llmw health [--brief]` | 뒤에서 돌아가는 부분들이 다 제대로 설정됐는지 확인합니다 |
| `llmw graph build` / `llmw graph export --format json\|html` | 메모들이 서로 어떻게 링크되는지 보여주는 지도를 만들거나 내보냅니다 |

## 기본 안전 규칙

- `raw/`에 있는 원본 자료는 절대 바꿀 수 없습니다. 이 도구는 그냥 거부합니다.
- 메모를 바꿀 때는 항상 짧은 이유를 함께 남겨야 하고, 이 이유는 영구 기록에 저장됩니다.
- "삭제"라는 건 없습니다. "보관"만 있을 뿐이죠. 메모를 옆으로 옮기고 표지판을 남겨서, 아무것도 그냥 사라지지 않게 합니다.
- 여러 변경 사항을 한꺼번에 적용할 때는 항상 먼저 백업하고, 중간에 문제가 생기면 자동으로 되돌립니다.
- 간단한 잠금 파일이 있어서, 이 도구 두 개가 동시에 같은 메모를 건드리다 서로 덮어쓰는 일을 막아줍니다.

## 더 많은 문서

| 문서 | 담긴 내용 |
|---|---|
| [docs/ko/installation.md](docs/ko/installation.md) | Windows, macOS, Linux별 전체 설치 방법, 업데이트·제거 방법 |
| [docs/ko/hooks.md](docs/ko/hooks.md) | Claude Code 플러그인이 AI가 위키를 건너뛰지 못하게 막고, 스스로 최신 상태를 유지하는 방법 |
| [docs/ko/commands.md](docs/ko/commands.md) | 검색이 내부적으로 실제 어떻게 동작하는지 |
| [docs/ko/project-layout.md](docs/ko/project-layout.md) | 위키 폴더를 정리하는 여러 방법, 이미 만들어 둔 위키를 그대로 쓰는 방법, 노트 앱 Obsidian과 함께 쓰는 방법 |
| [docs/ko/development.md](docs/ko/development.md) | `llmw` 자체를 개발하기 위한 환경 설정 |

## 라이선스

MIT — [LICENSE](LICENSE) 참조.
