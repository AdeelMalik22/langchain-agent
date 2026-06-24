from mcp import StdioServerParameters, stdio_client, ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools

class UniClient:
    def __init__(self):
        self.params = StdioServerParameters(
            command="python",
            args=["mcp_core/mcp_servers/uni_backend_server.py"]
        )

    async def __aenter__(self):
        self.client = stdio_client(self.params)
        self.read, self.write = await self.client.__aenter__()

        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()

        self.tools = await load_mcp_tools(self.session)

        return self.session, self.tools

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.__aexit__(exc_type, exc, tb)
        await self.client.__aexit__(exc_type, exc, tb)