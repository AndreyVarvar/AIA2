# JPEG compression
from dct import dct2d, idct2d
from rle import rle, irle
from huffman import *
import numpy as np
import json
import pickle
import matplotlib.image as mtimg
import matplotlib.pyplot as plt

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

EOB = (0, 0)   # end of block
ZRL = (15, 0)  # special: 16 consecutive zeros


def zigzag_scan(matrix: np.array):
    if matrix.size == 0:
        return []

    m, n = len(matrix), len(matrix[0])
    result = []
    for d in range(m + n - 1):
        temp = []
        # Determine the starting point of the diagonal
        if d < n:
            row = 0
            col = d
        else:
            row = d - n + 1
            col = n - 1
        # Collect elements along the diagonal
        while row < m and col >= 0:
            temp.append(matrix[row][col])
            row += 1
            col -= 1
        # Reverse every other diagonal for zig-zag pattern
        if d % 2 == 0:
            result.extend(temp[::-1])
        else:
            result.extend(temp)
    return result


def jpeg(image_path):
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
    
    def quantize(blocks: np.ndarray, table: np.ndarray) -> np.ndarray:
        """Divide DCT coefficients by quantization table and round."""
        return np.round(blocks / table).astype(np.int32)
    
    def zigzag(blocks: np.ndarray) -> np.ndarray:
        """Reorder each 8x8 block into a 64-element zigzag sequence.
        Input:  (nH, nW, 8, 8)
        Output: (nH, nW, 64)
        """
        return blocks.reshape(*blocks.shape[:2], 64)[:, :, ZIGZAG]
    
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
    
    def encode_channel(blocks: np.ndarray) -> tuple[list, list]:
        """Delta-encode DCs and RLE-encode ACs for a full channel.
        blocks shape: (nH, nW, 64)
        Returns dc_deltas and ac_symbols per block."""
        nH, nW = blocks.shape[:2]
        flat = blocks.reshape(-1, 64)

        # DC: store difference from previous block's DC
        dcs = flat[:, 0]
        dc_deltas = np.diff(dcs, prepend=0).tolist()

        # AC: RLE per block
        ac_symbols = [rle_encode_block(block) for block in flat]

        return dc_deltas, ac_symbols


    image = mtimg.imread(image_path)
    # step 1: convert RGB into YCbCr
    image = rgb_to_ycrcb(image)
    # step 2: Chroma subsampling (reduce resoulution od Cb and Cr)
    channels = subsample(image)
    # step 3: block splitting (8x8)
    blocks = [split_blocks(pad(ch)) for ch in channels]
    # step 4: apply 2D DCT for each block
    dct_blocks = [dct2d(b) for b in blocks]
    # step 5: quantization
    quant_blocks = [
        quantize(dct_blocks[0], Q_LUMA),
        quantize(dct_blocks[1], Q_CHROMA),
        quantize(dct_blocks[2], Q_CHROMA)
    ]
    zz_blocks = [zigzag(b) for b in quant_blocks]
    # step 6: RLE encodng
    encoded = [encode_channel(b) for b in zz_blocks]
    # step 7: huffman encoding


def ijpeg(jpeg_path):
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
    
    def dequantize(blocks: np.ndarray, table: np.ndarray) -> np.ndarray:
        """Multiply quantized coefficients back by quantization table."""
        return (blocks * table).astype(np.float32)
    
    def izigzag(blocks: np.ndarray) -> np.ndarray:
        """Restore zigzag sequence back to 8x8 block.
        Input:  (nH, nW, 64)
        Output: (nH, nW, 8, 8)
        """
        return blocks[:, :, ZIGZAG_INV].reshape(*blocks.shape[:2], 8, 8)
    
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
    
    def decode_channel(dc_deltas: list, ac_symbols: list, nH: int, nW: int) -> np.ndarray:
        """Reconstruct (nH, nW, 64) blocks from DC deltas and AC symbols."""
        dcs = np.cumsum(dc_deltas).astype(np.int32)
        blocks = np.array([
            rle_decode_block(ac, dc)
            for ac, dc in zip(ac_symbols, dcs)
        ])
        return blocks.reshape(nH, nW, 64)


if __name__ == "__main__":
    image_path = "AIA2\\tests\\to_compress.png"
    jpeg(image_path)
