# 훅: 에이전트를 정직하게, CLI를 동기화 상태로 유지

[English](../en/hooks.md) · **한국어** · [日本語](../ja/hooks.md) · [简体中文](../zh-Hans/hooks.md) · [Español](../es/hooks.md) · [Français](../fr/hooks.md)

Claude Code 플러그인([installation.md](installation.md) 참조)은 두 개의 훅을 설치합니다. 둘 다 `llmw`를 사용하는 데 필수는 아닙니다. 이미 자체 안전 규칙을 적용하는 CLI 위에 계층화된 편의사항입니다. 훅이 실행되었는지 여부와 관계없이.

## PreToolUse: 위키 가드

아무것도 에이전트가 Claude Code 스킬을 무시하고 대신 자신의 파일 편집 도구로 `wiki/*.md` 또는 `raw/**`를 직접 편집하는 것을 막을 수 없습니다. 이렇게 하면 `--reason` 감사 로그, 프론트매터 검증, 자동 백업을 건너뜁니다. 다른 경쟁 명령문 집합이 활성화되고 `llmw`를 언급하지 않을 때마다 실제로 발생합니다.

Claude Code 플러그인으로 설치되었을 때(순수 `llmw init` 프로젝트 스킬이 아님), `PreToolUse` 훅이 하네스 수준에서 그 간격을 좁힙니다: 네이티브 `Edit`/`Write`/`NotebookEdit` 호출이 `wiki/*.md` 또는 `raw/**`를 대상으로 하면 거부됩니다(또는 구성당 확인 프롬프트로 변환됨). 거부 메시지는 대신 실행할 정확한 `llmw` 명령을 명시합니다. 따라서 에이전트의 다음 동작은 일방 통행이 아닌 한 줄 재작성입니다.

가드는 `Edit`/`Write`/`NotebookEdit` 호출을 확인할 때만 보입니다. 대상이 실제 llmw 프로젝트의 `wiki/*.md` 또는 `raw/**`로 확인됩니다(파일에서 올라가며 `llmw`가 자신의 프로젝트 루트를 찾는 방식과 동일). 다른 모든 것(일반 `Read` 포함)은 건드리지 않고 통과하며, `Bash` 명령을 절대 검사하지 않습니다(셸 문자열 감시는 자체 거짓 양성 지뢰밭이므로 `wiki/log.md`의 감사 추적과 `llmw lint`는 훅이 이 간격을 차단하려고 하지 않고 감지 계층으로 유지됩니다).

`.llmw/config.toml`에서 프로젝트당 구성하거나 비활성화하세요:

```toml
[hooks]
wiki_guard = "deny"  # 기본값: 차단, llmw 수정을 이름으로 명시
# wiki_guard = "ask"   # 확인 프롬프트로 차단하는 대신
# wiki_guard = "off"   # 이 프로젝트에 대해 가드 비활성화
```

두 훅 모두 Windows에서 Git Bash를 요구합니다(Git Bash가 설치되지 않으면 Claude Code는 PowerShell로 폴백하고, 이 셸 형태 훅은 지원되지 않습니다). 다른 곳에서는 `llmw` 자체의 안전 게이트(이유 필요, 경로 제한, 프론트매터 검증, 쓰기 전 백업)가 훅이 실행되었는지 여부와 관계없이 여전히 적용됩니다.

또한 각 세션에서 짧은 `SessionStart` 메모를 컨텍스트에 드롭합니다: `.llmw`가 이미 있으면 "이 프로젝트에는 llmw wiki가 있습니다"(페이지 수 포함), 또는 아직 없으면 한 줄의 "run `llmw init`" 힌트입니다. 따라서 프로젝트 `CLAUDE.md`가 없고 위키가 전혀 초기화되지 않은 빈 환경도 첫 번째 턴에 `llmw`를 발견합니다.

## SessionStart: 자동 치유 CLI 설치

`plugin/bin/llmw`는 번들된 Python 배포판이 아닌 얇은 디스패처입니다. PATH의 실제 `llmw`로 외부 프로세스를 시작합니다. 마켓플레이스에서 플러그인을 업데이트하면 플러그인 자신의 파일만 업데이트됩니다(스킬, 훅). 스탠드얼론 바이너리는 **건드리지 않습니다**. 혼자 두면 플러그인 업데이트를 설치하면 아래에서 실행 중인 이전 CLI를 조용히 떠날 수 있습니다.

`SessionStart` 훅(`plugin/hooks/session-start.sh`, `plugin/hooks/hooks.json`을 통해 배선됨)이 그 간격을 좁힙니다: 모든 세션에서 설치된 `llmw --version`을 이 플러그인 번들이 선언하는 버전(`plugin/.claude-plugin/plugin.json`)과 비교합니다. 불일치가 있으면 — "전혀 설치되지 않음" 포함 — `uv tool install --force`를 통해 (재)설치하고(Git` 태그에 고정됨 `git+...@v<version>`로 폴백 `pip install --user --force-reinstall`), 플러그인 마켓플레이스 업데이트도 별도 수동 `uv tool upgrade llmw` 없이 스탠드얼론 CLI 바이너리를 동기화 상태로 가져옵니다.

버전이 이미 일치하면 확인은 각 세션마다 로컬 `llmw --version` 호출(네트워크 없음)일 뿐입니다. 재설치 경로는 진정한 버전 드리프트에서만 실행됩니다. 대략 릴리스당 한 번.
