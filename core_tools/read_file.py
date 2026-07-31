def read_file(filename: str, start_line: int = 0, n: int = 1) -> str:
    """Read a file {filename} and return the n lines starting from start_line.
    Args:
        filename: filename to read from
        start_line: line to start reading from.
        n: number of lines to read
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for _ in range(start_line):
                if not f.readline():
                    break
            lines = ''
            for _ in range(n):
                line = f.readline()
                if not line:
                    break
                lines+= line + ''
        return f"Successfully read the file'{filename}': the requested lines are {lines}."
    except Exception as e:
        return f"An unexpected error occurred while reading file '{filename}': {str(e)}"