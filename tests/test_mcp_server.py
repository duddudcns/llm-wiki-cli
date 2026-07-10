import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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
