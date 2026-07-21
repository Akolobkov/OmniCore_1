import os
def list_tools() -> str:
    """
    Lists all tool files in the created_tools directory.
    You can include them using 'include_tool' and use them

    Returns:
        str: List of available tool files
    """
    tools_dir = "created_tools"
    if not os.path.exists(tools_dir):
        return "ERROR: created_tools directory not found"

    available = []
    for file in os.listdir(tools_dir):
        if file.endswith('.py') and not file.startswith('__'):
            available.append(file.replace('.py', ''))

    if not available:
        return "No tools found in created_tools directory. You can create some using write_to_file function"

    return f"Available tools: {', '.join(available)}"