import importlib
import os
import sys
import inspect
def include_tool(tool_name: str) -> str:
    """Include a tool {tool_name} from "created_tools" directory
    Args:
        tool_name (str): name of the tool (not path to it)
    """
    tool_file_path = f"created_tools/{tool_name}.py"
    if not os.path.exists(tool_file_path):
        return f"ERROR: Tool file '{tool_file_path}' not found"
    try:
        module_name = f"created_tools.{tool_name}"
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)
        functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                # Skip imported functions from other modules
                if obj.__module__ == module_name:
                    functions.append((name, obj))
        if not functions:
            return f"ERROR: No functions found in {tool_name}.py"
        func_name, func = functions[0]
        import __main__
        if hasattr(__main__, 'tools'):
            existing_funcs = [t.__name__ for t in __main__.tools if hasattr(t, '__name__')]
            if func_name in existing_funcs:
                return f"INFO: Tool '{func_name}' is already included"

            __main__.tools.append(func)

            return f"SUCCESS: Tool '{func_name}' from '{tool_name}.py' has been included. Available tools now: {len(__main__.tools)} tools total"
        else:
            return "ERROR: Global tools list not found in main module"

    except Exception as e:
        return f"ERROR: Failed to include tool '{tool_name}': {str(e)}"