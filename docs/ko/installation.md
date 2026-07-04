# 설치

[English](../en/installation.md) · **한국어** · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · [Français](../fr/installation.md)

## 권장: Claude Code 플러그인

Claude Code에서 `llmw`를 사용한다면, 플러그인으로 설치하세요. 이것이 권장 경로이며 별도의 `pip`/`uv`/`pipx` 단계가 필요하지 않습니다:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(비대화형 동등물: `claude plugin marketplace add duddudcns/llm-wiki-cli`
그리고 `claude plugin install llm-wiki@llm-wiki-cli`)

이것은 Claude Code 스킬과 두 개의 훅을 설치합니다. 훅은 스탠드얼론 `llmw` 바이너리를 설치되고 동기화 상태로 자동 유지하며, 에이전트가 이를 우회하는 것을 방지합니다 — 정확히 어떤 훅이 무엇을 하는지, 어떻게 구성하는지는 [hooks.md](hooks.md)를 참조하세요. CLI 설치를 직접 관리하려면 이를 건너뛰고 대신 아래 방법 중 하나를 사용하세요. 충돌하지 않습니다. 둘 다 설치할 수도 있습니다.

## 스탠드얼론 CLI

Claude Code 외부(스크립팅, CI, 다른 에디터/에이전트)에서 `llmw`를 원하거나, 플러그인의 자동 치유 훅 대신 업그레이드를 직접 제어하려면 이를 선택하세요.

`llmw`는 **Python 3.11 이상**이 필요하며, 아직 PyPI에 없어서 패키지 인덱스 대신 이 저장소에서 직접 설치됩니다. **이 저장소는 현재 비공개입니다** — 설치(어떤 방법이든)는 인증된 자신의 `git`이 필요합니다(예: `gh auth login`을 통해 이미 로그인되었거나, GitHub 계정에 SSH 키가 있음). 저장소 접근 권한이 없는 사람은 부분 설치가 아닌 페치 오류를 받습니다.

아래의 모든 방법은 다른 Python 프로젝트의 의존성을 건드리지 않고 전역 `llmw` 명령을 제공합니다.

### Windows

먼저 Python 버전을 확인하세요(PowerShell 또는 Git Bash):

```powershell
python --version
```

3.11+가 없나요?

```powershell
winget install Python.Python.3.12
```

또는 [python.org/downloads](https://www.python.org/downloads/)에서 인스톨러를 다운로드하세요.

그 후, [uv](https://docs.astral.sh/uv/)를 사용하여(권장 — 빠르고 별도 pipx 설치 불필요):

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/):

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 일반 pip(현재 활성화된 모든 Python 환경에 설치 — venv를 사용하지 않으면 전역으로 설치):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Code 플러그인의 훅([hooks.md](hooks.md) 참조)은 Windows에서 Git Bash를 필요로 합니다. Git Bash가 설치되지 않으면 Claude Code는 PowerShell로 폴백하고, 이 셸 형태 훅은 지원되지 않습니다. `llmw` 자체의 안전 게이트는 어느 쪽이든 여전히 적용됩니다. 훅의 추가 편의성만 영향을 받습니다.

### macOS

먼저 Python 버전을 확인하세요:

```bash
python3 --version
```

3.11+가 없나요?

```bash
brew install python@3.12
```

그 후, [uv](https://docs.astral.sh/uv/)를 사용하여(권장):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 일반 pip:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

먼저 Python 버전을 확인하세요:

```bash
python3 --version
```

3.11+가 없나요?

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

그 후, [uv](https://docs.astral.sh/uv/)를 사용하여(권장):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/):

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 일반 pip:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### 로컬 클론, 편집 가능 설치(`llmw` 자체에 기여)

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # 모든 테스트가 통과하는 것으로 표시되어야 함
```

나머지 개발 워크플로우는 [development.md](development.md)를 참조하세요.

### 확인

```bash
llmw --version
llmw --help
```

### 업그레이드

```bash
uv tool upgrade llmw           # uv를 통해 설치한 경우
pipx upgrade llmw              # pipx를 통해 설치한 경우
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # 일반 pip
```

(Claude Code 플러그인을 사용하는 경우, 마켓플레이스에서 플러그인을 업그레이드하면 스탠드얼론 CLI도 자동으로 동기화됩니다 — [hooks.md](hooks.md) 참조.)

### 제거

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
