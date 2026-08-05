class tool_registry:
    registry = []
    def register_tool(self, func):
        self.registry.append(func)
    def list_tools(self):
        return self.registry
    def __len__(self):
        return len(self.registry)
registry = tool_registry()