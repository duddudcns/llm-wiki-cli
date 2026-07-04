# 개발

[English](../en/development.md) · **한국어** · [日本語](../ja/development.md) · [简体中文](../zh-Hans/development.md) · [Español](../es/development.md) · [Français](../fr/development.md)

개발 환경을 설정하려면 [installation.md](installation.md)의 "로컬 클론, 편집 가능 설치" 섹션을 참조하세요. `pytest`는 거기에서 테스트 스위트를 실행합니다.

## Claude Code 스킬

`llmw init`은 프로젝트에 `.claude/skills/llm-wiki/{SKILL.md,reference.md,examples.md}`를 작성합니다. Claude Code는 이것을 일반 스킬로 자동 검색합니다. 설치 단계 없음. 에이전트에게 `llmw`에 언제 도달할지, 핵심 검색 우선 워크플로우, 그리고 항상 로드된 `SKILL.md`를 짧게 유지하기 위해 전체 세부정보는 `reference.md`/`examples.md`를 가리킵니다.

llm-wiki Claude Code 플러그인이 마켓플레이스에서 이미 설치되어 있으면 이 프로젝트 로컬 복사를 건너뛰려면 `--no-claude-plugin`을 전달하세요. 그렇지 않으면 프로젝트는 동일한 스킬의 두 복사본(마켓플레이스 플러그인과 이 스킬)을 끝내고, 이는 중복입니다. Claude Code가 둘 다 로드할 때 혼동할 수 있습니다.

## MVP 범위

의도적으로 제외: MCP 서버, 데몬/감시 모드, 임베딩/벡터 검색, 직접 PDF/DOCX 파싱, Obsidian 플러그인, 웹 UI, 임의의 자동 병합/자동 삭제/모순 감지 논리.
