import heapq
from collections import Counter
import struct


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


def pad_bit_stream(bit_stream):
    padding = (8 - len(bit_stream) % 8) % 8
    extra = '0' * padding
    padding_info = '{0:08b}'.format(padding)
    return padding_info + bit_stream + extra

def binary_string_to_bit_stream(binary_str, padding):
    bit_stream = [binary_str[i] for i in range(len(binary_str))]
    bit_stream = [f"{i:08b}" for i in bit_stream]
    bit_stream = ''.join(bit_stream)
    bit_stream = bit_stream[:-padding]

    return bit_stream

def huffman_file(ipath, opath):
    with open(ipath, "r") as file:
        data = file.read()

    encoded, codes = huffman(data)
    
    encoded = pad_bit_stream(encoded)
    
    alphabet = list(codes.keys())
    representations = ''.join([codes[c] for c in alphabet])
    alphabet = ''.join(alphabet)

    representations = pad_bit_stream(representations)

    with open(opath, "wb") as file:
        file.write(struct.pack("B", len(alphabet)))  # write alphabet size
        for c in alphabet:   # write the alphabet
            file.write(c.encode("ascii"))
        # write the sizes of each character representations
        for c in alphabet:
            file.write(struct.pack("B", len(codes[c])))
        # write the representations
        for i in range(0, len(representations), 8):
            file.write(struct.pack("B", int(representations[i:i+8], 2)))
        # write the compressed message
        for i in range(0, len(encoded), 8):
            file.write(struct.pack("B", int(encoded[i:i+8], 2)))

def ihuffman_file(ipath, opath):
    with open(ipath, "rb") as file:
        data = file.read()

    alphabet_size = data[0]
    off = 1
    alphabet = []
    for i in range(off, off+alphabet_size):
        alphabet.append(chr(data[i]))
    off += alphabet_size
    
    sizes = []
    for i in range(off, off+alphabet_size):
        sizes.append(data[i])
    off += alphabet_size

    padding = data[off]
    off += 1
    representations = data[off:off+(sum(sizes)+padding)//8]
    representations = binary_string_to_bit_stream(representations, padding)
    off += (sum(sizes)+padding)//8

    codes = {}
    for i in range(len(sizes)):
        codes[alphabet[i]] = representations[sum(sizes[:i]):sum(sizes[:i+1])]

    padding = data[off]
    off += 1
    encoded = data[off:]
    encoded = binary_string_to_bit_stream(encoded, padding)
    
    result = ihuffman(encoded, codes)

    with open(opath, "w") as file:
        file.write(result)
