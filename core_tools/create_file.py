
def create_file(filename: str, content: str) -> str:
    """Create a file {filename} and write the provided content to it.
    The first line will be set to ensure UTF-8 encoding declaration.
    Important: DO NOT forget to write the extension in the filename!
    Example: 'tool.py' - RIGHT, 'tool' - WRONG
    Important: THE FILE NAMR AND TOOL FUNCTION NAME INSIDE MUST BE THE SAME!!!
    Example: 'tool.py': 'def tool()' - RIGHT, 'tool.py': 'def do_something()' - WRONG
    Args:
        filename: filename to create file with
        content: The actual Python code content to be written.
    """
    # Prepend the mandatory encoding declaration
    filename = "created_tools/"+str(filename)
    encoded_content = "# -*- coding: utf-8 -*-\n" + content
    #if '.py' not in filename:
    #    filename = filename + ".py"
    try:
        with open(filename, "x", encoding="utf-8") as f:
            f.write(encoded_content)
        return f"Successfully created and populated the file '{filename}'."
    except FileExistsError:
        return f"File with such name already exists: {filename}. Tool creation failed."
    except Exception as e:
        return f"An unexpected error occurred while creating file '{filename}': {str(e)}"