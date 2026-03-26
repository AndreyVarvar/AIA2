def rle(string: str, len_first: bool = True) -> str:
        if string is None or len(string) == 0:
            return ""
        result = ""
        prev = string[0]
        count = 1

        for i in range(1, len(string)):
            if string[i] == prev:
                count += 1
            else:
                result += f"{count}{prev}" if len_first else f"{prev}{count}"
                prev = string[i]
                count = 1
        else:
            result += f"{count}{prev}" if len_first else f"{prev}{count}"
        
        return result


def irle(string: str, len_first: bool) -> str:
        if string is None or len(string) == 0:
            return ""
        
        result = ""

        for i in range(0, len(string), 2):
            result += string[i + 1] * int(string[i]) if len_first else string[i] * int(string[i + 1])
        
        return result