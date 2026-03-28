
# JPEG compression
from src.dct import dct2d, idct2d
from src.rle import rle, irle
from src.huffman import *
import numpy as np
import pygame as pg
import json
import pickle
pg.init()


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
        Y  =  0.299  * R + 0.587  * G + 0.114  * B - 128
        Cb = -0.169  * R - 0.331  * G + 0.500  * B
        Cr =  0.500  * R - 0.419  * G - 0.081  * B

        return np.stack([Y, Cb, Cr], axis=-1).clip(0, 255).astype(np.uint8)
    
    def subsample(img: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Split YCbCr into channels, downsample Cb and Cr by 2x in both dims."""
        Y  = img[..., 0]
        Cb = img[..., 1]
        Cr = img[..., 2]

        # Average each 2x2 block into one pixel (box filter)
        Cb_sub = (Cb[0::2, 0::2] + Cb[1::2, 0::2] +
                Cb[0::2, 1::2] + Cb[1::2, 1::2]) / 4
        Cr_sub = (Cr[0::2, 0::2] + Cr[1::2, 0::2] +
                Cr[0::2, 1::2] + Cr[1::2, 1::2]) / 4

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

        return np.pad(channel, ((0, ph), (0, pw)), mode='edge')

    image = np.array(pg.image.load(image_path))
    # step 1: convert RGB into YCbCr
    image = rgb_to_ycrcb(image)
    # step 2: Chroma subsampling (reduce resoulution od Cb and Cr)
    channels = subsample(image)
    # step 3: block splitting (8x8)
    blocks = [split_blocks(pad(ch)) for ch in channels]
    # step 4: apply 2D DCT for each block
    dct_blocks = [dct2d(b) for b in blocks]

    # luma_q_matrix = [
    #     [5,  4,  5,  5,  6,  8,  15, 21],
    #     [4,  4,  5,  6,  7,  11, 19, 27],
    #     [4,  5,  5,  7,  11, 16, 23, 27],
    #     [5,  6,  8,  9,  17, 19, 25, 28],
    #     [8,  8,  12, 15, 20, 24, 30, 32],
    #     [12, 17, 17, 25, 31, 30, 35, 29],
    #     [15, 18, 20, 23, 30, 33, 34, 30],
    #     [18, 16, 17, 18, 22, 27, 29, 29]
    # ]

    # color_q_matrix = [
    #     [6,  6,  8,  14, 29, 29, 29, 29],
    #     [6,  7,  8,  19, 29, 29, 29, 29],
    #     [8,  8,  17, 29, 29, 29, 29, 29],
    #     [14, 19, 29, 29, 29, 29, 29, 29],
    #     [29, 29, 29, 29, 29, 29, 29, 29],
    #     [29, 29, 29, 29, 29, 29, 29, 29],
    #     [29, 29, 29, 29, 29, 29, 29, 29],
    #     [29, 29, 29, 29, 29, 29, 29, 29]
    # ]
    
        

    # step 2: convert to frequency domain using DCT
    # first divide the channel information into 8x8 chunks
    # x_rem = image.width  % 8
    # y_rem = image.height % 8
    # for block_x in range(0, image.width, 8):
    #     for block_y in range(0, image.height, 8):
    #         # transfer data to the block matrix
    #         block = np.zeros((8, 8))
    #         for rel_x in range(0, min(8, image.width-block_x)):
    #             for rel_y in range(0, min(8, image.height-block_y)):
    #                 block[rel_y][rel_x] = channel[block_y+rel_y][block_x+rel_x]
    #         # apply DCT transform to block
    #         block_dct = dct2d(block)
            
    #         # step 3: quantization matrix
    #         q_matrix = color_q_matrix
    #         if i == 0:
    #             q_matrix = luma_q_matrix

    #         for x in range(8):
    #             for y in range(8):
    #                 block_dct[y][x] = round(block_dct[y][x] / q_matrix[y][x])

    #         # step 4: MAXIMUM COMPRESSION
    #         data_strip = zigzag_scan(block_dct)
    #         str_data_strip = ' '.join(map(str, data_strip))
    #         rle_encoded = rle(str_data_strip)
    #         huffman_encoded, huffman_codes = huffman(rle_encoded)
    #         # make the huffman_encoded part length be divisible by 4
    #         results.append([huffman_encoded, huffman_codes])

    # image_name = image_path.split('/')[-1].split('.')[0]
    # with open(f"./results/{image_name}.jpeg", "wb") as file:
    #     for encoded, codes in results:
    #         padding = (8 - len(encoded) % 8) % 8
    
    #         encoded += '0'*padding  # add extra 0's to the end to make the length divisible by 8
    #         file.write(bytes([padding]))
    #         byte_array = bytearray([int(encoded[i:i+8], 2) for i in range(0, len(encoded), 8)])
    #         file.write(byte_array)

def ijpeg(jpeg_path):
    """Convert compressend JPEG image back to PNG with losses because of nature of JPEG"""

    def ycbcr_to_rgb(img: np.ndarray) -> np.ndarray:
        """Convert a YCbCr image (H, W, 3) uint8 back to RGB uint8."""
        img = img.astype(np.float32)
        Y, Cb, Cr = img[..., 0] + 128, img[..., 1], img[..., 2]

        R = Y             + 1.402  * Cr
        G = Y - 0.344  * Cb - 0.714  * Cr
        B = Y + 1.772  * Cb

        return np.stack([R, G, B], axis=-1).clip(0, 255).astype(np.uint8)
    
    def upsample(Y: np.ndarray, Cb: np.ndarray, Cr: np.ndarray) -> np.ndarray:
        """Upsample Cb and Cr back to full resolution by repeating pixels."""
        Cb_up = np.repeat(np.repeat(Cb, 2, axis=0), 2, axis=1)
        Cr_up = np.repeat(np.repeat(Cr, 2, axis=0), 2, axis=1)

        # Crop to Y's shape in case of odd dimensions
        h, w = Y.shape
        return np.stack([Y, Cb_up[:h, :w], Cr_up[:h, :w]], axis=-1)
