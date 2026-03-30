def rle_jpeg(data: str) -> str:
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


def irle_jpeg(data: str) -> str:
    """Decode a run-length encoded string back to space-separated floats."""
    if not data.strip():
        return ""

    tokens = []
    for run in data.split():
        value, count = run.rsplit(":", 1)  # rsplit to safely handle negative values
        tokens.extend([value] * int(count))

    return " ".join(tokens)


def rle(data: str):
    result = ""

    if len(data) == 0:
        return ""

    c = data[0]
    prev_c = c
    run_length = 1

    for i in range(1, len(data)):
        c = data[i]

        if prev_c != c or run_length == 127:
            if run_length == 1 and ord(c) < 128:
                result += prev_c
            else:
                result += chr(run_length + 128)  # convert run_length into one byte character. Add 128 to not confuse with normal characters
                result += prev_c

            run_length = 1
            prev_c = c
        else:
            run_length += 1  # no need to set prev_c, since it did not change


    if run_length == 1 and ord(c) < 128:
        result += prev_c
    else:
        result += chr(run_length + 128)  # convert run_length into one byte character. Add 128 to not confuse with normal characters
        result += prev_c

    return result


def irle(data: str):
    result = ""
    i = 0
    while i < len(data):
        c = data[i]
        if ord(c) >= 128:  # this is run_length
            run_length = ord(c) - 128
            i += 1
            c = data[i]
            result += c * run_length

        else:
            result += c

        i += 1

    return result



def rle_file(ipath, opath):
    with open(ipath, "r") as file:
        data = file.read()

    result = rle(data)

    with open(opath, "w") as file:
        file.write(result)

def irle_file(ipath, opath):
    with open(ipath, "r") as file:
        data = file.read()

    result = irle(data)

    with open(opath, "w") as file:
        file.write(result)

