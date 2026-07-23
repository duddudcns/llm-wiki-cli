import asyncio
import inspect
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llmw import mcp_server


def _server_params() -> StdioServerParameters:
    # Spawn `python -m llmw.mcp_server` with the *current* interpreter
    # rather than the bare `llmw-mcp` command name — a bare name resolves
    # via PATH, which on a dev machine can hit a globally `uv tool
    # install`-ed llmw pinned to an old released version instead of this
    # checkout's editable install, silently testing the wrong code.
    return StdioServerParameters(command=sys.executable, args=["-m", "llmw.mcp_server"])


def test_llmw_search_default_limit_matches_cli_and_docs() -> None:
    # mcp_server.llmw_search used to default to limit=10 while the CLI's
    # `llmw search` and every doc describing it default to 5 — same query,
    # different result-count depending on which surface answered it.
    assert inspect.signature(mcp_server.llmw_search).parameters["limit"].default == 5


def test_mcp_initialize_list_and_meaningful_call(tmp_path: Path) -> None:
    async def exercise() -> None:
        params = _server_params()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "llm-wiki"
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {
                    "llmw_init", "llmw_status", "llmw_search", "llmw_read", "llmw_write",
                    "llmw_edit", "llmw_patch", "llmw_archive", "llmw_related", "llmw_links",
                    "llmw_backlinks", "llmw_lint", "llmw_health", "llmw_ingest", "llmw_graph",
                }
                result = await session.call_tool("llmw_init", {"path": str(tmp_path)})
                assert not result.isError
                assert (tmp_path / ".llmw").is_dir()
                status = await session.call_tool("llmw_status", {"root": str(tmp_path)})
                assert not status.isError
                assert status.structuredContent["wiki_page_count"] >= 3

    asyncio.run(exercise())


def test_mcp_edit_patch_archive_round_trip(tmp_path: Path) -> None:
    async def exercise() -> None:
        params = _server_params()
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.call_tool("llmw_init", {"path": str(tmp_path)})

                written = await session.call_tool(
                    "llmw_write",
                    {
                        "path": "wiki/notes/scratch.md",
                        "content": "---\ntitle: Scratch\n---\n\nOriginal body.\n",
                        "reason": "seed page for MCP round-trip test",
                        "root": str(tmp_path),
                    },
                )
                assert not written.isError

                edited = await session.call_tool(
                    "llmw_edit",
                    {
                        "path": "wiki/notes/scratch.md",
                        "old": "Original body.",
                        "new": "Edited body.",
                        "reason": "test llmw_edit",
                        "root": str(tmp_path),
                    },
                )
                assert not edited.isError
                assert edited.structuredContent["edited"] is True
                assert "Edited body." in (tmp_path / "wiki/notes/scratch.md").read_text()

                patched = await session.call_tool(
                    "llmw_patch",
                    {
                        "path": "wiki/notes/scratch.md",
                        "diff": (
                            "--- a/wiki/notes/scratch.md\n"
                            "+++ b/wiki/notes/scratch.md\n"
                            "@@ -1,5 +1,6 @@\n"
                            " ---\n"
                            " title: Scratch\n"
                            " ---\n"
                            " \n"
                            "-Edited body.\n"
                            "+Edited body.\n"
                            "+Patched line.\n"
                        ),
                        "reason": "test llmw_patch",
                        "root": str(tmp_path),
                    },
                )
                assert not patched.isError
                assert "Patched line." in (tmp_path / "wiki/notes/scratch.md").read_text()

                lint = await session.call_tool("llmw_lint", {"root": str(tmp_path)})
                assert not lint.isError
                assert "clean" in lint.structuredContent

                health = await session.call_tool("llmw_health", {"root": str(tmp_path)})
                assert not health.isError
                assert "healthy" in health.structuredContent

                graph = await session.call_tool("llmw_graph", {"root": str(tmp_path)})
                assert not graph.isError
                assert "nodes" in graph.structuredContent

                archived = await session.call_tool(
                    "llmw_archive",
                    {
                        "path": "wiki/notes/scratch.md",
                        "reason": "test llmw_archive",
                        "root": str(tmp_path),
                    },
                )
                assert not archived.isError
                assert archived.structuredContent["archived"] is True

    asyncio.run(exercise())
