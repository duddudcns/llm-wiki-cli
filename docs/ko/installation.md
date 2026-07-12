# 설치

[English](../en/installation.md) · **한국어** · [日本語](../ja/installation.md) · [简体中文](../zh-Hans/installation.md) · [Español](../es/installation.md) · [Français](../fr/installation.md)

## 추천 방법: Claude Code 플러그인

Claude Code에서 `llmw`를 쓸 거라면 플러그인으로 설치하세요. 가장
추천하는 방법이고, 따로 `pip`/`uv`/`pipx` 단계를 거칠 필요도 없습니다:

```
/plugin marketplace add duddudcns/llm-wiki-cli
/plugin install llm-wiki@llm-wiki-cli
```

(터미널에서 직접 실행하고 싶다면: `claude plugin marketplace add duddudcns/llm-wiki-cli`
와 `claude plugin install llm-wiki@llm-wiki-cli`)

이렇게 설치하면 안전장치 네 가지도 함께 들어옵니다. 하나는 커맨드라인
도구 자체를 자동으로 최신 상태로 유지해 주고, 다른 하나는 AI가 위키를
건너뛰고 파일을 직접 고치지 못하게 막아주고, 나머지 둘은 새 작업을
시작하기 전에 위키를 먼저 검색하고 작업이 끝나면 위키를 업데이트하도록
AI에게 알려줍니다. 정확히 어떤 기능인지, 원하지 않으면 어떻게 끄는지는
[hooks.md](hooks.md)를 보세요. 커맨드라인 도구를 직접 설치해서 업데이트도
손수 관리하고 싶다면, 이건 건너뛰고 아래 방법 중 하나를 쓰면 됩니다.
서로 충돌하지 않으니 둘 다 설치해도 됩니다.

## Codex 플러그인

`uvx`가 포함된 [uv](https://docs.astral.sh/uv/)를 설치한 뒤 다음을 실행하세요.

```text
codex plugin marketplace add duddudcns/llm-wiki-cli
codex plugin add llm-wiki@llm-wiki-cli
```

`codex plugin list`로 확인하세요. 플러그인은 고정된 GitHub 릴리스에서
MCP 서버를 `uvx`로 자동 실행하므로 `llmw` CLI를 별도로 설치할 필요는
없습니다. `uvx --version`이 안 되면 [uv](https://docs.astral.sh/uv/)부터
설치하세요. Codex는 Claude Code 플러그인의 훅 파일을 실행하지 않습니다 —
Codex 자체의 별도 PreToolUse/Stop 훅(같은 검색-전/업데이트-후 알림을
Codex의 도구 체계에 맞게 이식한 것)을 대신 씁니다. 이 훅들이 처음 쓸 때
백그라운드에서 고정 버전의 `llmw` CLI를 자동 설치해 두므로, 직접 터미널에서
쓰려는 경우에만 아래 CLI 설치를 추가로 진행하면 됩니다.

## 커맨드라인 도구만 설치하기 (플러그인 없이)

Claude Code 밖에서 `llmw`를 쓰고 싶다면 이 방법을 고르세요. 스크립트나
자동화 파이프라인, 다른 에디터·도구와 함께 쓸 때 적합합니다.

`llmw`는 **Python 3.11 이상**이 필요합니다. 아직 공개 패키지 저장소에
올라가 있지 않아서, 대신 이 GitHub 저장소에서 바로 설치합니다. **이
저장소는 현재 비공개(private)입니다** — 어떤 방법으로 설치하든 자신의
GitHub 로그인이 `git`에 연결돼 있어야 합니다(예를 들어 이미
`gh auth login`으로 로그인해 두었거나, GitHub 계정에 SSH 키를 등록해
둔 경우). 이게 안 돼 있으면 설치가 실패하면서 이유를 명확히 알려줍니다.
뭔가 망가진 채로 설치되는 일은 없습니다.

아래 방법은 어떤 걸 선택해도 컴퓨터 어디서든 실행할 수 있는 `llmw`
명령어가 만들어지고, 컴퓨터에 있는 다른 Python 프로젝트에는 영향을
주지 않습니다.

### Windows

먼저 어떤 버전의 Python이 있는지 확인하세요 (PowerShell이나 Git Bash에서):

```powershell
python --version
```

아직 3.11 이상이 없다면:

```powershell
winget install Python.Python.3.12
```

또는 [python.org/downloads](https://www.python.org/downloads/)에서
설치 파일을 내려받으세요.

그다음, [uv](https://docs.astral.sh/uv/)를 쓴다면(추천 — 빠르고, 별도로
pipx를 설치할 필요도 없습니다):

```powershell
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/)를 쓴다면:

```powershell
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 그냥 pip로 설치한다면(현재 컴퓨터에서 쓰고 있는 Python 환경에
그대로 설치됩니다 — 이게 정말 원하는 방식일 때만 쓰세요):

```powershell
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

> Claude Code 플러그인의 안전장치 기능(자세한 내용은 [hooks.md](hooks.md))은
> Windows에서 동작하려면 "Git Bash"가 설치돼 있어야 합니다. 없다면
> 그 추가 기능들만 실행되지 않을 뿐, `llmw` 자체는 문제없이 동작하고
> 자체 안전 점검도 그대로 유지됩니다.

### macOS

먼저 어떤 버전의 Python이 있는지 확인하세요:

```bash
python3 --version
```

아직 3.11 이상이 없다면:

```bash
brew install python@3.12
```

그다음, [uv](https://docs.astral.sh/uv/)를 쓴다면(추천):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/)를 쓴다면:

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 그냥 pip로 설치한다면:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### Linux

먼저 어떤 버전의 Python이 있는지 확인하세요:

```bash
python3 --version
```

아직 3.11 이상이 없다면:

```bash
sudo apt install python3.12 python3.12-venv   # Ubuntu/Debian
sudo dnf install python3.12                   # Fedora
```

그다음, [uv](https://docs.astral.sh/uv/)를 쓴다면(추천):

```bash
uv tool install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 [pipx](https://pipx.pypa.io/)를 쓴다면:

```bash
pipx install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

또는 그냥 pip로 설치한다면:

```bash
pip install "git+https://github.com/duddudcns/llm-wiki-cli.git"
```

### `llmw` 자체를 개발하고 싶다면

```bash
git clone https://github.com/duddudcns/llm-wiki-cli.git
cd llm-wiki-cli
python3 -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
                                # Windows git-bash:   source .venv/Scripts/activate
pip install -e ".[dev]"
pytest                         # 모든 테스트가 통과해야 합니다
```

기여하는 방법은 [development.md](development.md)에서 더 자세히 볼 수 있습니다.

### 잘 설치됐는지 확인하기

```bash
llmw --version
llmw --help
```

### 업데이트하기

```bash
uv tool upgrade llmw           # uv로 설치했다면
pipx upgrade llmw              # pipx로 설치했다면
pip install --upgrade --force-reinstall "git+https://github.com/duddudcns/llm-wiki-cli.git"   # 그냥 pip라면
```

(Claude Code 플러그인을 설치했다면, 마켓플레이스에서 플러그인을
업데이트할 때 커맨드라인 도구도 자동으로 함께 업데이트됩니다 —
[hooks.md](hooks.md) 참고.)

### 제거하기

```bash
uv tool uninstall llmw
pipx uninstall llmw
pip uninstall llmw
```
