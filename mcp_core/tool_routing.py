

class ToolRouter:
    def __init__(self, tool_session_map):
        self.tool_session_map = tool_session_map

    async def call(self, tool_name, args):
        session = self.tool_session_map.get(tool_name)

        if not session:
            raise Exception(f"No session found for tool: {tool_name}")

        return await session.call_tool(tool_name, args)