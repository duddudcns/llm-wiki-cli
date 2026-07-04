# 프로젝트 레이아웃, 기존 위키 도입, Obsidian 호환성

[English](../en/project-layout.md) · **한국어** · [日本語](../ja/project-layout.md) · [简体中文](../zh-Hans/project-layout.md) · [Español](../es/project-layout.md) · [Français](../fr/project-layout.md)

## 프로젝트 레이아웃: 클래식 vs `ai-wiki/`

기본적으로(`--layout classic`) `raw/`, `wiki/`, `.llmw/`는 프로젝트 루트에 직접 앉습니다. 대신 `--layout ai-wiki`를 전달하여 한 수준 아래에 중첩시켜 루트를 깔끔하게 유지하세요:

```bash
llmw init --layout ai-wiki
```

```text
ai-wiki/
  raw/ wiki/ .llmw/            # 클래식 레이아웃과 동일한 콘텐츠, 중첩됨
.claude/skills/llm-wiki/       # 실제 프로젝트 루트에서 여전히 구성됨
.claude-plugin/plugin.json     # 실제 프로젝트 루트에서 여전히 구성됨
```

모든 명령은 프로젝트가 사용하는 레이아웃을 자동 감지합니다. 먼저 프로젝트 루트에서 `.llmw/`를 확인한 다음 `ai-wiki/.llmw`로 폴백합니다. 기존 클래식 레이아웃 프로젝트는 마이그레이션이 필요하지 않습니다.

프로젝트를 현재 디렉토리에서 자동 감지할 수 없는 경우(예: 다른 곳에서 실행되는 스크립트 또는 비표준 체크아웃), `--root <path>` 또는 `LLMW_ROOT` 환경 변수로 명시적으로 `llmw`를 가리키세요. 둘 다 두 레이아웃에 대해 확인되므로 단일 값으로 충분합니다(개별적으로 `raw/`/`wiki/`/`.llmw/`를 지정할 필요 없음):

```bash
llmw --root /path/to/project status
LLMW_ROOT=/path/to/project llmw status
```

## 기존 위키 도입

`raw/`/`wiki/`(또는 `ai-wiki/` 중첩 동등물)이 이미 자체 규칙(예: `llmw` 이전에 존재했던 손으로 말린 Karpathy 패턴 위키)에 따라 실제 콘텐츠를 가지고 있으면 일반 `init` 대신 `--adopt`를 사용하세요:

```bash
llmw init --adopt                  # 또는: llmw init --layout ai-wiki --adopt
```

`--adopt`는 첫 번째 실행에서 `.llmw/`와 `config.toml`을 만듭니다. 기본 콘텐츠 파일(`raw/README.md`, `wiki/index.md`, `wiki/overview.md`, `wiki/log.md`) 또는 기본 분류 서브폴더(`entities/`, `concepts/`, `decisions/`, `syntheses/`, `projects/`, `glossary/`, `archived/`, `sources/`) — **`--force`를 사용하더라도** — 를 절대 작성합니다. 따라서 이러한 경로의 기존 콘텐츠는 절대 건드리거나 덮어쓰지 않습니다. `config.toml`이 있으면 `--force`는 다시 기본값으로 재작성하지 않으므로 도입 스키마에 대한 손으로 튜닝된 재정의(아래 참조)가 재`init --adopt --force`를 유지합니다. 일반 `llmw init`(no `--adopt`)은 항상 이러한 기본값을 구성하고, `--force`에 덮어쓰고, `--force`에서도 `config.toml`을 기본값으로 재설정합니다. 빈 디렉토리(또는 이미 llmw 관리) 디렉토리에만 사용하세요. 기존 스키마 특이성(예: `created`/`updated` 대신 `last_updated` 필드, 또는 `wiki/` 외부 루트 수준 `index.md`/`log.md` 파일)은 `.llmw/config.toml`의 `lint.required_frontmatter`와 `paths.extra_root_pages`를 통해 처리됩니다. 아래를 참조하세요.

## llmw를 기존 위키에 적응

위키가 이미 자체 규칙(다른 프론트매터 필드, `wiki/` 외부에 있는 최상위 파일)을 가지고 있으면 위키의 파일을 재구성하는 대신 `llmw init --adopt`를 루트에 가리키고(위 참조) `.llmw/config.toml`을 조정하세요:

```toml
[paths]
# 위키/**/*.md와 함께 인덱싱할 추가 개별 마크다운 파일(프로젝트 루트 기준)
# 예: 위키/ 외부에 보관되는 스키마/인덱스/로그 파일.
extra_root_pages = ["index.md", "log.md", "schema.md"]

[lint]
# `llmw lint`가 필요로 하는 프론트매터 키 재정의. 기본값은
# ["type", "status", "created", "updated"]; "updated"도 수락합니다
# `last_updated` 키.
required_frontmatter = ["type", "status", "last_updated"]
```

기존 페이지는 변경할 필요가 없습니다. `llmw rebuild`는 다음 실행 시 새 구성을 선택합니다.

## Obsidian 호환성

`wiki/`는 YAML 프론트매터와 `[[wikilinks]]`를 가진 평문 마크다운입니다. 그것을 그래프 보기, 백링크, 검색을 위해 GUI로 Obsidian 볼트로 직접 열기 위해, CLI 드리븐 에이전트 워크플로우를 포기하지 않고.

링크 해석은 특히 실제 Obsidian 내보내기 특이성을 처리합니다:

- `[[Page]]`, `[[Page|Alias]]`, `[[Page#Heading|Alias]]`, `[[#Heading]]`, `![[Embed]]` — 전체 위키링크 문법.
- 경로와 유사한 위키링크 대상(`[[concepts/foo]]`)은 **vault root**(`wiki/`)를 기준으로 확인합니다. 실제로 `wiki/`를 볼트로 열 때 Obsidian이 이들을 확인하는 방식과 일치합니다. 링크 페이지 자신의 폴더 기준이 아닙니다.
- `related:` 프론트매터는 첫 번째 클래스 링크 소스입니다. 인라인 위키링크와 동일합니다. 평문 경로/제목(`related: [wiki/concepts/foo]`, 일부 위키가 `llmw` 도입 전에 사용했던 규칙) 및 Obsidian 자신의 Properties 패널 형식(`related: ["[[Note]]"]`) 모두 올바르게 확인됩니다.
- URL로 인코딩된 대상(`[Profile](Project%20Profile.md)`, 파일 이름이 공백이 있을 때 흔함)이 있는 마크다운 링크는 온디스크 페이지에 대해 일치하기 전에 디코딩됩니다.
- `wiki/` 외부를 가리키는 상대 위키링크(예: `[[../notes/x]]`)는 실제 파일 시스템에 대해 확인됩니다. 인덱스된 위키 페이지가 아니어서가 아니라 대상이 프로젝트의 어디에도 실제로 존재하지 않을 때만 `llmw lint`에 의해 깨진 것으로 보고됩니다.

**그래프가 의도적으로 Obsidian 자신과 다른 곳**: `related:` 에지와 llmw의 제목 기반 위키링크 해석(`[[Exact Page Title]]`이 파일 이름과 일치하지 않을 때도 확인)은 모두 Obsidian과 동등한 것이 없는 llmw 확장입니다. Obsidian 자신의 그래프 보기는 이러한 에지를 표시하지 않습니다. 다른 폴더의 동일한 파일 이름 스템을 가진 두 페이지도 두 도구에서 모호하게 확인됩니다(첫 번째 일치 우승). `wiki/`를 Obsidian에서 열면 같은 파일의 실제 유용한 그래프를 얻습니다. 픽셀 동일한 것은 아닙니다.
