class MCPManager:
    def __init__(self, clients):
        self.clients = clients
        self.sessions = []
        self.tools = []
        self.tool_session_map = {}

    async def __aenter__(self):
        for client in self.clients:
            session, tools = await client.__aenter__()

            self.sessions.append(session)

            server_name = client.__class__.__name__.replace("Client", "").lower()

            for t in tools:
                original_name = t.name

                self.tool_session_map[original_name] = session

            self.tools.extend(tools)

        return self.sessions, self.tools, self.tool_session_map

    async def __aexit__(self, exc_type, exc, tb):
        for client in self.clients:
            await client.__aexit__(exc_type, exc, tb)