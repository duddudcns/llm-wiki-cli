# `llmw`에 기여하기

[English](../en/development.md) · **한국어** · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

개발 환경을 만드는 방법은 [installation.md](installation.md)의
"`llmw` 자체를 개발하고 싶다면" 부분을 보세요. 거기서 `pytest`를
실행하면 테스트가 전부 돌아갑니다.

## Claude Code 스킬은 이렇게 동작합니다

`llmw init`은 프로젝트 안의 `.claude/skills/llm-wiki/`에 파일 몇 개를
써 넣습니다. Claude Code는 이 파일들을 자동으로 인식하기 때문에 따로
설치할 필요가 없습니다. 이 파일들은 AI에게 `llmw`를 언제, 어떻게
써야 하는지 알려주는데, 매번 모든 세부사항을 다 불러오지 않아도
되도록 되어 있습니다.

이미 마켓플레이스에서 Claude Code 플러그인을 설치했다면, `llmw init`을
실행할 때 `--no-claude-plugin`을 붙여서 이 추가 복사본을 만들지 않게
하세요. 안 그러면 똑같은 안내가 두 벌 생기는데, 이건 불필요할 뿐만
아니라 오히려 헷갈릴 수 있습니다.

`llmw init`은 `--no-claude-plugin`을 붙이든 안 붙이든 상관없이
`.claude/rules/llm-wiki.md`는 항상 씁니다. Claude Code 플러그인
매니페스트는 훅이나 스킬은 배포할 수 있어도 `.claude/rules/` 내용은
배포할 방법이 없기 때문에, 매 세션에 작업 전 검색·작업 후 업데이트
안내를 자동으로 컨텍스트에 실어주는 유일한 경로가 이것뿐이고,
마켓플레이스 플러그인과 중복될 일도 없습니다.

`llmw init`은 같은 안내를 `.codex/rules/llm-wiki.md`에도 매번 써 넣습니다. 
어느 플러그인을 쓰든(또는 아무것도 안 쓰든) 상관없이 말입니다 — Codex 플러그인 
매니페스트도 Claude Code의 것처럼 "훅이나 스킬은 배포 가능하지만 규칙 파일은 
불가능한" 한계가 있기 때문입니다. Codex 전용 플래그 뒤에 숨기지 않고 항상 써 넣는 
이유는, 팀이 Claude Code와 Codex를 섞어 쓰는 경우 추가 설정 없이 둘 다 바로 
준비가 되도록 하려는 것입니다. 안 쓰는 규칙 파일은 해가 없으니까요.

## 이 도구가 일부러 하지 않는 것들 (아직은)

의도적으로 다루지 않는 범위입니다: AI 모델과 직접 연결하기, 파일
변경을 자동으로 감시하기, AI 기반 의미 검색, PDF/Word 파일을 직접
읽기, 그래픽 앱, 메모를 자동으로 합치거나 지우거나 충돌을 자동으로
해결하는 기능.
