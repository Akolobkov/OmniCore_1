import importlib
import os
import sys
import inspect
def include_tool(tool_name: str) -> str:
    """Include a tool {tool_name} from "created_tools" directory
    IMPORTANT: DO NOT INCLUDE '.py' IN 'tool_name'!!!
    Args:
        tool_name (str): name of the tool (not path to it)
    """
    # The full expected module name structure in sys.path
    module_name = f"created_tools.{tool_name}"
    tool_file_path = f"created_tools/{tool_name}.py"

    if not os.path.exists(tool_file_path):
        return f"ERROR: Tool file '{tool_file_path}' not found."

    try:
        # Attempt to dynamically import the module
        module = None
        if module_name in sys.modules:
            # If already loaded, reload it
            module = importlib.reload(sys.modules[module_name])
            return f"Module reloaded from '{module_name}'."
        else:
            try:
                # Import module, handling potential system/runtime errors during loading
                module = importlib.import_module(module_name)
            except Exception as e:
                return f"CRITICAL IMPORT ERROR: Could not load tool '{tool_name}' from '{module_name}'. Error: {str(e)}. Check dependencies or file syntax."

        functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                if getattr(obj, '__module__', None) == module_name:
                    functions.append((name, obj))

        if not functions:
            return f"ERROR: No public functions found in {tool_name}.py or they are imported/private."

        # Assuming the first function is the intended main tool for simplicity
        func_name, func = functions[0]

        import __main__

        existing_funcs = [t.__name__ for t in __main__.tools if hasattr(t, '__name__')]
        if func_name in existing_funcs:
            return f"INFO: Tool '{func_name}' is already included. No action taken."

        # WARNING: Modifying global state directly in the tool function is brittle
        __main__.tools.append(func)

        return (f"SUCCESS: Tool '{func_name}' from '{tool_name}.py' has been successfully imported and included. "
                f"The system now recognizes {len(__main__.tools)} tools total.")

    except Exception as e:
        # Catch any remaining unexpected exceptions during the process
        return f"SEVERE ERROR: Failed to include tool '{tool_name}'. An unexpected error occurred during processing: {type(e).__name__} - {str(e)}"