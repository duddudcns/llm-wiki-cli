import asyncio
import inspect
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llmw import mcp_server


def test_llmw_search_default_limit_matches_cli_and_docs() -> None:
    # mcp_server.llmw_search used to default to limit=10 while the CLI's
    # `llmw search` and every doc describing it default to 5 — same query,
    # different result-count depending on which surface answered it.
    assert inspect.signature(mcp_server.llmw_search).parameters["limit"].default == 5


def test_mcp_initialize_list_and_meaningful_call(tmp_path: Path) -> None:
    async def exercise() -> None:
        params = StdioServerParameters(command="llmw-mcp")
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "llm-wiki"
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {
                    "llmw_init", "llmw_status", "llmw_search", "llmw_read", "llmw_write"
                }
                result = await session.call_tool("llmw_init", {"path": str(tmp_path)})
                assert not result.isError
                assert (tmp_path / ".llmw").is_dir()
                status = await session.call_tool("llmw_status", {"root": str(tmp_path)})
                assert not status.isError
                assert status.structuredContent["wiki_page_count"] >= 3

    asyncio.run(exercise())
