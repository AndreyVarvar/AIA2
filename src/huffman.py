import heapq
from collections import Counter


class HuffmanNode:
    def __init__(self, symbol=None, freq=None):
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        if self.freq < other.freq:
            return True
        else:
            return False


def _build_huffman_tree(symbols):
    freq = Counter(symbols)
    heap = [HuffmanNode(sym, f) for sym, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = HuffmanNode(freq=left.freq + right.freq)
        parent.left = left
        parent.right = right
        heapq.heappush(heap, parent)

    if heap:
        return heap[0]
    else:
        return None

def _generate_huffman_codes(node, code="", table=None):
    if table is None:
        table = {}
    if node:
        if node.symbol is not None:
            table[node.symbol] = code if code else "0"
        _generate_huffman_codes(node.left, code + "0", table)
        _generate_huffman_codes(node.right, code + "1", table)
    return table

def huffman(symbols):
    tree = _build_huffman_tree(symbols)
    codes = _generate_huffman_codes(tree)
    encoded = ''.join(codes[s] for s in symbols)
    return encoded, codes

def ihuffman(encoded, codes):
    decoded = ""
    inverted_codes = {v: k for k, v in codes.items()}

    current = ''

    for bit in encoded:
        current += bit
        if current in inverted_codes:
            decoded += inverted_codes[current]
            current = ""

    return decoded

def ihuffman_jpeg(encoded: str, codes: dict) -> list:
    """List-returning version of ihuffman for JPEG use."""
    inverted_codes = {v: k for k, v in codes.items()}
    decoded = []
    current = ""
    for bit in encoded:
        current += bit
        if current in inverted_codes:
            decoded.append(inverted_codes[current])
            current = ""
    return decoded