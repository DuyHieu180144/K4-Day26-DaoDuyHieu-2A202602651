"""Test client connecting directly to the remote Weather MCP Server (Streamable HTTP).

Verifies that:
1. The FastMCP server is reachable at MCP_SERVER_URL (default: http://localhost:8085/mcp)
2. Tool discovery (list_tools) exposes get_current_weather, get_forecast, and health_check
3. Tool execution (call_tool) works properly across the transport
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure utf-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client


async def test_weather_mcp() -> None:
    print(f"Connecting to Weather MCP server at: {SERVER_URL}")
    http_client = create_mcp_http_client()

    async with http_client:
        async with streamable_http_client(SERVER_URL, http_client=http_client) as streams:
            read, write = streams[0], streams[1]
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected and initialized MCP session!\n")

                # 1. Discover tools
                tools_response = await session.list_tools()
                print("Discovered tools from MCP server:")
                for tool in tools_response.tools:
                    print(f"  - {tool.name}: {tool.description.splitlines()[0] if tool.description else ''}")
                print()

                # 2. Call health_check
                print("--- Calling health_check() ---")
                res_health = await session.call_tool("health_check", {})
                print(res_health.content[0].text.strip())
                print()

                # 3. Call get_current_weather for Hanoi
                print("--- Calling get_current_weather(city='Hanoi') ---")
                res_weather = await session.call_tool("get_current_weather", {"city": "Hanoi"})
                print(res_weather.content[0].text.strip())
                print()

                # 4. Call get_forecast for Brisbane
                print("--- Calling get_forecast(city='Brisbane', days=2) ---")
                res_forecast = await session.call_tool("get_forecast", {"city": "Brisbane", "days": 2})
                print(res_forecast.content[0].text.strip())
                print()

                print("All remote MCP tool calls executed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(test_weather_mcp())
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
        print("Tip: Make sure mcp-server is running first: python weather.py")
        sys.exit(1)
