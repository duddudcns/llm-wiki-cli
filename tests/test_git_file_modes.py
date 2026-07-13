"""Guards the executable bit on shell scripts invoked directly by hooks.json.

Claude Code and Codex run hook commands as a bare path (e.g.
`${CLAUDE_PLUGIN_ROOT}/hooks/stop.sh`), not `sh <path>` — on Unix that
requires the file to carry the executable bit in git's tracked mode, or
every hook silently no-ops (fail-open, so nothing surfaces the breakage).
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
