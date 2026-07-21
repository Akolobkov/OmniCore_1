
def create_file(filename: str, content: str) -> str:
    """Create a file {filename} and write the provided content to it.
    The first line will be set to ensure UTF-8 encoding declaration.
    Args:
        filename: filename to create file with
        content: The actual Python code content to be written.
    """
    # Prepend the mandatory encoding declaration
    filename = "created_tools/"+str(filename)
    encoded_content = "# -*- coding: utf-8 -*-\n" + content
    if '.py' not in filename:
        filename = filename + ".py"
    try:
        with open(filename, "x") as f:
            f.write(encoded_content)
        return f"Successfully created and populated the file '{filename}'."
    except FileExistsError:
        return f"File with such name already exists: {filename}. Tool creation failed."
    except Exception as e:
        return f"An unexpected error occurred while creating file '{filename}': {str(e)}"