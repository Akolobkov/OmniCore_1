def write_to_file(text: str, filename: str) -> str:
    f"""write into EXISTING file {filename} any text or code
    Note: This function uses write mode ('w'), meaning it will OVERWRITE 
    any existing content in the specified file.
    Args:
        text: text
        filename: filename to write to
    """
    try:
        with open(filename, "w") as f:
            f.write(text)
        return "Succesfully wrote the text into file"
    except FileNotFoundError:
        return "file with such name not found"
    except IOError as e:
        return f"ERROR: Could not write to file '{filename}'. Reason: {e}"