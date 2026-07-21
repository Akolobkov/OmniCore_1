def write_to_file(text: str, filename: str) -> str:
    f"""write into file {filename} any text or code
    'IMPORTANT: After creating a new tool ALWAYS include it!!!'
    Args:
        text: text
        filename: filename to write to
    """
    try:
        f = open(filename, "w")
        f.write(text)
        return "Succesfully wrote the text into file"
    except FileNotFoundError:
        return "file with such name not found"