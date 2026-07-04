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

## 이 도구가 일부러 하지 않는 것들 (아직은)

의도적으로 다루지 않는 범위입니다: AI 모델과 직접 연결하기, 파일
변경을 자동으로 감시하기, AI 기반 의미 검색, PDF/Word 파일을 직접
읽기, 그래픽 앱, 메모를 자동으로 합치거나 지우거나 충돌을 자동으로
해결하는 기능.
