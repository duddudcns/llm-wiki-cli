"""Guards the executable bit on the shell scripts this repo distributes.

hooks.json now invokes SessionStart as `bash <path>` and calls `llmw hook
<event>` directly for every other event, so Windows never resolves a bare
`.sh` path through ShellExecute. The remaining scripts stay executable
anyway: `plugin/bin/llmw` is run as a bare path, and the hook wrappers are
kept as manual entry points and as a fallback for hosts that can only take
a script path. Without the executable bit in git's tracked mode those
invocations silently no-op on Unix (fail-open, so nothing surfaces the
breakage).
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXECUTABLE_SCRIPTS = [
    "plugin/bin/llmw",
    "plugin/hooks/pre-tool-use.sh",
    "plugin/hooks/session-start.sh",
    "plugin/hooks/stop.sh",
    "plugin/hooks/user-prompt-submit.sh",
    "plugins/llm-wiki/hooks/pre-tool-use.sh",
    "plugins/llm-wiki/hooks/session-start.sh",
    "plugins/llm-wiki/hooks/stop.sh",
]


def test_hook_scripts_are_executable_in_git_index() -> None:
    output = subprocess.run(
        ["git", "ls-files", "-s", *EXECUTABLE_SCRIPTS],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # `git ls-files -s` sorts its output alphabetically, not by argument
    # order, and each line is "<mode> <hash> <stage>\t<path>".
    modes_by_path = {}
    for line in output.splitlines():
        meta, path = line.split("\t", 1)
        mode = meta.split(" ", 1)[0]
        modes_by_path[path] = mode
    assert set(modes_by_path) == set(EXECUTABLE_SCRIPTS), (
        f"expected {EXECUTABLE_SCRIPTS}, git tracked {sorted(modes_by_path)}"
    )
    for path in EXECUTABLE_SCRIPTS:
        assert modes_by_path[path] == "100755", (
            f"{path} is tracked as {modes_by_path[path]}, expected 100755 (executable)"
        )
