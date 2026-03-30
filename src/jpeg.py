# JPEG compression
from dct import dct2d, idct2d
from rle import rle, irle
from huffman import *
import numpy as np
import json
import pickle
import matplotlib.image as mtimg
import struct

# Quantization table for brightness
Q_LUMA = np.array(
    [
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99],
    ],
    dtype=np.float32,
)

# Quantization table for color
Q_CHROMA = np.array(
    [
        [17, 18, 24, 47, 99, 99, 99, 99],
        [18, 21, 26, 66, 99, 99, 99, 99],
        [24, 26, 56, 99, 99, 99, 99, 99],
        [47, 66, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
    ],
    dtype=np.float32,
)

# Arrays used for zigzag sorting
ZIGZAG = np.array([
     0,  1,  5,  6, 14, 15, 27, 28,
     2,  4,  7, 13, 16, 26, 29, 42,
     3,  8, 12, 17, 25, 30, 41, 43,
     9, 11, 18, 24, 31, 40, 44, 53,
    10, 19, 23, 32, 39, 45, 52, 54,
    20, 22, 33, 38, 46, 51, 55, 60,
    21, 34, 37, 47, 50, 56, 59, 61,
    35, 36, 48, 49, 57, 58, 62, 63,
], dtype=np.int32)

ZIGZAG_INV = np.argsort(ZIGZAG)

EOB = (0, 0)  # end of block
ZRL = (15, 0)  # special: 16 consecutive zeros

def _sym_to_str(sym) -> str:
    """Convert a JPEG symbol (int or tuple) to a unique string key."""
    if isinstance(sym, tuple):
        return f"{sym[0]},{sym[1]}"
    return str(sym)

def _str_to_sym(s: str, is_ac: bool):
    """Convert a string key back to a JPEG symbol."""
    if is_ac:
        a, b = s.split(',')
        return (int(a), int(b))
    return int(s)

def jpeg(ipath, opath):
    """Convert PNG image into JPEG"""

    def rgb_to_ycrcb(img: np.ndarray) -> np.ndarray:
        """Convert an RGB image (H, W, 3) uint8 to YCbCr uint8."""
        img = img.astype(np.float32)

        R, G, B = img[..., 0], img[..., 1], img[..., 2]
        Y = 0.299 * R + 0.587 * G + 0.114 * B - 128
        Cb = -0.169 * R - 0.331 * G + 0.500 * B
        Cr = 0.500 * R - 0.419 * G - 0.081 * B

        return np.stack([Y, Cb, Cr], axis=-1).clip(0, 255).astype(np.uint8)

    def subsample(img: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Split YCbCr into channels, downsample Cb and Cr by 2x in both dims."""
        Y = img[..., 0]
        Cb = img[..., 1]
        Cr = img[..., 2]

        # Average each 2x2 block into one pixel (box filter)
        Cb_sub = (Cb[0::2, 0::2] + Cb[1::2, 0::2] + Cb[0::2, 1::2] + Cb[1::2, 1::2]) / 4
        Cr_sub = (Cr[0::2, 0::2] + Cr[1::2, 0::2] + Cr[0::2, 1::2] + Cr[1::2, 1::2]) / 4

        return Y, Cb_sub, Cr_sub

    def split_blocks(channel: np.ndarray) -> np.ndarray:
        """Split a 2D channel into non-overlapping 8x8 blocks.
        Returns shape (nH, nW, 8, 8) where nH/nW are the number of blocks."""
        h, w = channel.shape
        assert h % 8 == 0 and w % 8 == 0, "Channel dimensions must be multiples of 8"

        blocks = channel.reshape(h // 8, 8, w // 8, 8)
        blocks = blocks.transpose(0, 2, 1, 3)  # (nH, nW, 8, 8)

        return blocks

    def pad(channel: np.ndarray) -> np.ndarray:
        """Pad a channel to the nearest multiple of 8 by repeating edge pixels."""
        h, w = channel.shape
        ph = (8 - h % 8) % 8  # extra rows needed
        pw = (8 - w % 8) % 8  # extra cols needed

        return np.pad(channel, ((0, ph), (0, pw)), mode="edge")

    def apply_dct(blocks: np.ndarray) -> np.ndarray:
        nH, nW = blocks.shape[:2]
        result = np.empty_like(blocks, dtype=float)
        for i in range(nH):
            for j in range(nW):
                result[i, j] = dct2d(blocks[i, j])
        return result

    def quantize(blocks: np.ndarray, table: np.ndarray) -> np.ndarray:
        """Divide DCT coefficients by quantization table and round."""
        return np.round(blocks / table).astype(np.int32)

    def zigzag(blocks: np.ndarray) -> np.ndarray:
        """Reorder each 8x8 block into a 64-element zigzag sequence.
        Input:  (nH, nW, 8, 8)
        Output: (nH, nW, 64)
        """
        return blocks.reshape(*blocks.shape[:2], 64)[:, :, ZIGZAG]

    def encode_channel(blocks: np.ndarray) -> tuple[list, list]:
        """Delta-encode DCs and RLE-encode ACs for a full channel.
        blocks shape: (nH, nW, 64)
        Returns dc_deltas and ac_symbols per block."""

        def rle_encode_block(block: np.ndarray) -> list[tuple[int, int]]:
            """RLE encode 63 AC coefficients of a zigzag block."""
            symbols = []
            skip = 0
            for val in block[1:]:  # skip DC
                if val == 0:
                    skip += 1
                    if skip == 16:  # ZRL: can only encode runs of 15
                        symbols.append(ZRL)
                        skip = 0
                else:
                    symbols.append((skip, int(val)))
                    skip = 0
            if skip > 0:
                symbols.append(EOB)
            return symbols

        nH, nW = blocks.shape[:2]
        flat = blocks.reshape(-1, 64)

        # DC: store difference from previous block's DC
        dcs = flat[:, 0]
        dc_deltas = np.diff(dcs, prepend=0).tolist()

        # AC: RLE per block
        ac_symbols = [rle_encode_block(block) for block in flat]

        return dc_deltas, ac_symbols

    def huffman_dc(dc_deltas: list) -> tuple[str, dict]:
        symbols = [_sym_to_str(s) for s in dc_deltas]
        bits, codes = huffman(symbols)
        return bits, codes
    
    def huffman_ac(ac_symbols: list[list]) -> tuple[str, dict]:
        flat = [_sym_to_str(s) for block in ac_symbols for s in block]
        bits, codes = huffman(flat)
        return bits, codes
    
    def write_jpeg(path: str, encoded: dict) -> None:
        """Write encoded data to a binary file."""

        def bits_to_bytes(bits: str) -> bytes:
            """Pack a bitstring into bytes, padding the last byte with zeros."""
            padding = (8 - len(bits) % 8) % 8
            bits += '0' * padding
            result = bytearray()
            for i in range(0, len(bits), 8):
                result.append(int(bits[i:i+8], 2))
            return bytes([padding]) + bytes(result)  # first byte stores padding length
        
        def encode_sof(h: int, w: int) -> bytes:
            marker = b'\xff\xc0'
            length = (8 + 3 * 3).to_bytes(2, 'big')
            precision = b'\x08'
            height = h.to_bytes(2, 'big')
            width  = w.to_bytes(2, 'big')
            n_components = b'\x03'
            components = (
                b'\x01\x11\x00' +
                b'\x02\x11\x01' +
                b'\x03\x11\x01'
            )
            return marker + length + precision + height + width + n_components + components


        def encode_dht(dc_codes: dict, ac_codes: dict) -> bytes:
            marker = b'\xff\xc4'
            payload = json.dumps({
                'dc': {str(k): v for k, v in dc_codes.items()},
                'ac': {str(k): v for k, v in ac_codes.items()}
            }).encode('utf-8')
            length = (2 + len(payload)).to_bytes(2, 'big')
            return marker + length + payload

        with open(path, 'wb') as f:
            # SOI marker
            f.write(b'\xff\xd8')

            # SOF: original dimensions
            f.write(encode_sof(encoded['orig_h'], encoded['orig_w']))

            # block shapes (nH, nW per channel)
            for nH, nW in encoded['block_shapes']:
                f.write(struct.pack('>HH', nH, nW))  # 2 unsigned shorts, big endian

            # per channel: DHT + bitstream
            for dc_bits, dc_codes, ac_bits, ac_codes in encoded['results']:
                # Huffman tables
                f.write(encode_dht(dc_codes, ac_codes))

                # DC bitstream
                dc_data = bits_to_bytes(dc_bits)
                f.write(struct.pack('>I', len(dc_data)))  # length prefix
                f.write(dc_data)

                # AC bitstream
                ac_data = bits_to_bytes(ac_bits)
                f.write(struct.pack('>I', len(ac_data)))
                f.write(ac_data)

            # EOI marker
            f.write(b'\xff\xd9')

    image = mtimg.imread(ipath)
    orig_h, orig_w = image.shape[:2]
    # step 1: convert RGB into YCbCr
    ycbcr = rgb_to_ycrcb(image)
    # step 2: Chroma subsampling (reduce resoulution of Cb and Cr)
    channels = subsample(ycbcr)
    # step 3: block splitting (8x8)
    blocks = [split_blocks(pad(ch)) for ch in channels]
    block_shapes = [(b.shape[0], b.shape[1]) for b in blocks]
    # step 4: apply 2D DCT for each block
    dct_blocks = [apply_dct(b) for b in blocks]
    # step 5: quantization
    quant_blocks = [
        quantize(dct_blocks[0], Q_LUMA),
        quantize(dct_blocks[1], Q_CHROMA),
        quantize(dct_blocks[2], Q_CHROMA),
    ]
    # step 6: zigzag encoding
    zz_blocks = [zigzag(b) for b in quant_blocks]
    # step 7: RLE + huffman
    results = []
    for zz in zz_blocks:
        dc_deltas, ac_symbols = encode_channel(zz)
        dc_bits, dc_codes = huffman_dc(dc_deltas)
        ac_bits, ac_codes = huffman_ac(ac_symbols)
        results.append((dc_bits, dc_codes, ac_bits, ac_codes))

    encoded = {
        'results':      results,
        'block_shapes': block_shapes,
        'orig_h':       orig_h,
        'orig_w':       orig_w,
    }
    write_jpeg(opath, encoded)


def ijpeg(ipath, opath):
    """Convert compressend JPEG image back to PNG with losses because of nature of JPEG"""

    def ycbcr_to_rgb(img: np.ndarray) -> np.ndarray:
        """Convert a YCbCr image (H, W, 3) uint8 back to RGB uint8."""
        img = img.astype(np.float32)
        Y, Cb, Cr = img[..., 0] + 128, img[..., 1], img[..., 2]

        R = Y + 1.402 * Cr
        G = Y - 0.344 * Cb - 0.714 * Cr
        B = Y + 1.772 * Cb

        return np.stack([R, G, B], axis=-1).clip(0, 255).astype(np.uint8)

    def upsample(Y: np.ndarray, Cb: np.ndarray, Cr: np.ndarray) -> np.ndarray:
        """Upsample Cb and Cr back to full resolution by repeating pixels."""
        Cb_up = np.repeat(np.repeat(Cb, 2, axis=0), 2, axis=1)
        Cr_up = np.repeat(np.repeat(Cr, 2, axis=0), 2, axis=1)

        # Crop to Y's shape in case of odd dimensions
        h, w = Y.shape
        return np.stack([Y, Cb_up[:h, :w], Cr_up[:h, :w]], axis=-1)
    
    def merge_blocks(blocks: np.ndarray, h: int, w: int) -> np.ndarray:
        """Reconstruct a 2D channel from (nH, nW, 8, 8) blocks."""
        return (blocks.transpose(0, 2, 1, 3).reshape(h, w))
    
    def apply_idct(blocks: np.ndarray) -> np.ndarray:
        nH, nW = blocks.shape[:2]
        result = np.empty_like(blocks, dtype=float)
        for i in range(nH):
            for j in range(nW):
                result[i, j] = idct2d(blocks[i, j])
        return result

    def dequantize(blocks: np.ndarray, table: np.ndarray) -> np.ndarray:
        """Multiply quantized coefficients back by quantization table."""
        return (blocks * table).astype(np.float32)

    def izigzag(blocks: np.ndarray) -> np.ndarray:
        """Restore zigzag sequence back to 8x8 block.
        Input:  (nH, nW, 64)
        Output: (nH, nW, 8, 8)
        """
        return blocks[:, :, ZIGZAG_INV].reshape(*blocks.shape[:2], 8, 8)

    def decode_channel(dc_deltas: list, ac_symbols: list, nH: int, nW: int) -> np.ndarray:
        """Reconstruct (nH, nW, 64) blocks from DC deltas and AC symbols."""

        def rle_decode_block(symbols: list[tuple[int, int]], dc: int) -> np.ndarray:
            """Decode RLE symbols back to 64 coefficients including DC."""
            block = np.zeros(64, dtype=np.int32)
            block[0] = dc
            i = 1
            for skip, val in symbols:
                if (skip, val) == EOB:
                    break
                if (skip, val) == ZRL:
                    i += 16
                else:
                    i += skip
                    block[i] = val
                    i += 1
            return block
        
        dcs = np.cumsum(dc_deltas).astype(np.int32)
        blocks = np.array([rle_decode_block(ac, dc) for ac, dc in zip(ac_symbols, dcs)])
        return blocks.reshape(nH, nW, 64)

    def ihuffman_dc(bits: str, codes: dict) -> list:
        symbols = ihuffman(bits, codes)
        return [_str_to_sym(s, is_ac=False) for s in symbols]
    
    def ihuffman_ac(bits: str, codes: dict, n_blocks: int) -> list[list]:
        flat = ihuffman(bits, codes)
        flat = [_str_to_sym(s, is_ac=True) for s in flat]

        # re-split flat list back into blocks using EOB
        blocks = []
        block = []
        for sym in flat:
            block.append(sym)
            if sym == EOB or len(block) == 63:
                blocks.append(block)
                block = []
                if len(blocks) == n_blocks:
                    break
        return blocks
    
    def read_jpeg(path: str) -> dict:
        """Read encoded data back from a binary file."""

        def bytes_to_bits(data: bytes) -> str:
            """Unpack bytes back into a bitstring, removing padding."""
            padding = data[0]
            bits = ''.join(f'{b:08b}' for b in data[1:])
            return bits if padding == 0 else bits[:-padding]
        
        def decode_sof(data: bytes) -> tuple[int, int]:
            assert data[:2] == b'\xff\xc0', "Not a SOF0 marker"
            h = int.from_bytes(data[5:7], 'big')
            w = int.from_bytes(data[7:9], 'big')
            return h, w


        def decode_dht(data: bytes) -> tuple[dict, dict]:
            assert data[:2] == b'\xff\xc4', "Not a DHT marker"
            length = int.from_bytes(data[2:4], 'big')
            payload = json.loads(data[4:4 + length - 2].decode('utf-8'))
            dc_codes = {int(k) if k.lstrip('-').isdigit() else eval(k): v
                        for k, v in payload['dc'].items()}
            ac_codes = {eval(k): v for k, v in payload['ac'].items()}
            return dc_codes, ac_codes
        
        with open(path, 'rb') as f:
            data = f.read()

        pos = 0

        # SOI
        assert data[pos:pos+2] == b'\xff\xd8', "Missing SOI marker"
        pos += 2

        # SOF
        sof_length = int.from_bytes(data[pos+2:pos+4], 'big') + 2
        orig_h, orig_w = decode_sof(data[pos:pos+sof_length])
        pos += sof_length

        # block shapes
        block_shapes = []
        for _ in range(3):
            nH, nW = struct.unpack('>HH', data[pos:pos+4])
            block_shapes.append((nH, nW))
            pos += 4

        # per channel
        results = []
        for _ in range(3):
            # DHT
            dht_length = int.from_bytes(data[pos+2:pos+4], 'big') + 2
            dc_codes, ac_codes = decode_dht(data[pos:pos+dht_length])
            pos += dht_length

            # DC bitstream
            dc_len = struct.unpack('>I', data[pos:pos+4])[0]
            pos += 4
            dc_bits = bytes_to_bits(data[pos:pos+dc_len])
            pos += dc_len

            # AC bitstream
            ac_len = struct.unpack('>I', data[pos:pos+4])[0]
            pos += 4
            ac_bits = bytes_to_bits(data[pos:pos+ac_len])
            pos += ac_len

            results.append((dc_bits, dc_codes, ac_bits, ac_codes))

        # EOI
        assert data[pos:pos+2] == b'\xff\xd9', "Missing EOI marker"

        return {
            'results':      results,
            'block_shapes': block_shapes,
            'orig_h':       orig_h,
            'orig_w':       orig_w,
        }


    data = read_jpeg(ipath)

    results      = data['results']
    block_shapes = data['block_shapes']
    orig_h       = data['orig_h']
    orig_w       = data['orig_w']

    tables = [Q_LUMA, Q_CHROMA, Q_CHROMA]
    channels = []

    for (dc_bits, dc_codes, ac_bits, ac_codes), (nH, nW), table in zip(results, block_shapes, tables):

        # step 7: Huffman + RLE decode
        dc_deltas  = ihuffman_dc(dc_bits, dc_codes)
        ac_symbols = ihuffman_ac(ac_bits, ac_codes, nH * nW)
        zz = decode_channel(dc_deltas, ac_symbols, nH, nW)

        # step 6: inverse zigzag
        blocks = izigzag(zz)

        # step 5: dequantization
        blocks = dequantize(blocks, table)

        # step 4: IDCT
        blocks = apply_idct(blocks)

        # step 3: merge blocks
        channel = merge_blocks(blocks, nH * 8, nW * 8)

        channels.append(channel)

    # step 3: crop padding
    Y  = channels[0][:orig_h, :orig_w]
    Cb = channels[1][:orig_h // 2, :orig_w // 2]
    Cr = channels[2][:orig_h // 2, :orig_w // 2]

    # step 2: upsample chroma
    ycbcr = upsample(Y, Cb, Cr)

    # step 1: convert YCbCr back to RGB
    image =  ycbcr_to_rgb(ycbcr)

    mtimg.imsave(opath, image)


if __name__ == "__main__":
    ipath = "AIA2\\tests\\to_compress.png"
    opath = "AIA2\\results\\compressed.png"
    jpeg(ipath, opath)
