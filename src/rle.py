def rle(data: str) -> str:
    """Encode a string of space-separated floats using run-length encoding."""
    if not data.strip():
        return ""
    
    tokens = data.split()
    runs = []
    count = 1

    for i in range(1, len(tokens)):
        if tokens[i] == tokens[i - 1]:
            count += 1
        else:
            runs.append(f"{tokens[i - 1]}:{count}")
            count = 1

    runs.append(f"{tokens[-1]}:{count}")
    return " ".join(runs)


def irle(data: str) -> str:
    """Decode a run-length encoded string back to space-separated floats."""
    if not data.strip():
        return ""

    tokens = []
    for run in data.split():
        value, count = run.rsplit(":", 1)  # rsplit to safely handle negative values
        tokens.extend([value] * int(count))

    return " ".join(tokens)