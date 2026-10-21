"""Smoke-test mcp_server.py over stdio: list tools, run_model on smoke.py, get_state, measure."""
import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def main():
    p = StdioServerParameters(command=sys.executable, args=[os.path.join(CAD, "mcp_server.py")])
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("tools:", [t.name for t in (await s.list_tools()).tools])
            res = await s.call_tool("run_model", {"name": "mcp_smoke", "script_path": os.path.join(CAD, "examples", "smoke.py")})
            print(res.content[0].text[:600])
            res = await s.call_tool("measure", {"name": "mcp_smoke"})
            print(res.content[0].text)
            res = await s.call_tool("export", {"name": "mcp_smoke", "fmt": "step"})
            print(res.content[0].text)


asyncio.run(main())
