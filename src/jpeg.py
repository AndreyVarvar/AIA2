
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
    image = pg.image.load(image_path)
    # step 1: convert RGB into YCbCr

    coeff = [
        # [R coeff, B coeff, G coeff, offset]
        [0.299,    0.587,   0.114,  0  ],  # luma 
        [-0.1687, -0.3313,  0.5,    128],  # chroma blue
        [0.5,     -0.4187, -0.0813, 128]
    ]

    luma_q_matrix = [
        [5,  4,  5,  5,  6,  8,  15, 21],
        [4,  4,  5,  6,  7,  11, 19, 27],
        [4,  5,  5,  7,  11, 16, 23, 27],
        [5,  6,  8,  9,  17, 19, 25, 28],
        [8,  8,  12, 15, 20, 24, 30, 32],
        [12, 17, 17, 25, 31, 30, 35, 29],
        [15, 18, 20, 23, 30, 33, 34, 30],
        [18, 16, 17, 18, 22, 27, 29, 29]
    ]

    color_q_matrix = [
        [6,  6,  8,  14, 29, 29, 29, 29],
        [6,  7,  8,  19, 29, 29, 29, 29],
        [8,  8,  17, 29, 29, 29, 29, 29],
        [14, 19, 29, 29, 29, 29, 29, 29],
        [29, 29, 29, 29, 29, 29, 29, 29],
        [29, 29, 29, 29, 29, 29, 29, 29],
        [29, 29, 29, 29, 29, 29, 29, 29],
        [29, 29, 29, 29, 29, 29, 29, 29]
    ]

    results = []
    for i in range(3):
        channel = np.zeros((image.height, image.width))
        for x in range(image.width):
            for y in range(image.height):
                color = image.get_at((x, y))

                r, g, b = color.r, color.g, color.b
                k1, k2, k3, offset = coeff[i]
                channel[y][x] = k1*r + k2*g + k3*b + offset

        # step 2: convert to frequency domain using DCT
        # first divide the channel information into 8x8 chunks
        x_rem = image.width  % 8
        y_rem = image.height % 8
        for block_x in range(0, image.width, 8):
            for block_y in range(0, image.height, 8):
                # transfer data to the block matrix
                block = np.zeros((8, 8))
                for rel_x in range(0, min(8, image.width-block_x)):
                    for rel_y in range(0, min(8, image.height-block_y)):
                        block[rel_y][rel_x] = channel[block_y+rel_y][block_x+rel_x]
                # apply DCT transform to block
                block_dct = dct2d(block)
                
                # step 3: quantization matrix
                q_matrix = color_q_matrix
                if i == 0:
                    q_matrix = luma_q_matrix

                for x in range(8):
                    for y in range(8):
                        block_dct[y][x] = round(block_dct[y][x] / q_matrix[y][x])

                # step 4: MAXIMUM COMPRESSION
                data_strip = zigzag_scan(block_dct)
                str_data_strip = ' '.join(map(str, data_strip))
                rle_encoded = rle(str_data_strip)
                huffman_encoded, huffman_codes = huffman(rle_encoded)
                # make the huffman_encoded part length be divisible by 4
                results.append([huffman_encoded, huffman_codes])

    image_name = image_path.split('/')[-1].split('.')[0]
    with open(f"./results/{image_name}.jpeg", "wb") as file:
        for encoded, codes in results:
            padding = (8 - len(encoded) % 8) % 8
    
            encoded += '0'*padding  # add extra 0's to the end to make the length divisible by 8
            file.write(bytes([padding]))
            byte_array = bytearray([int(encoded[i:i+8], 2) for i in range(0, len(encoded), 8)])
            file.write(byte_array)

def ijpeg(jpeg_path):
    return
    # step 1: read the file
    with open(jpeg_path, "r") as file:
        data = file.read()
    # step 2: decompress the huffman part
    channels = data.split("\n")
    for channel in channels:
        encoded, tree_str = channel.split(" tree:")
        #print("-----------------------------------------")
        tree = json.loads(tree_str.replace("'", '"'))  # replace single quotes with double quotes, because json picky
        rle_encoded = ihuffman(encoded, tree)
        #print(rle_encoded)
        str_data_strip = irle(rle_encoded)
        data_strip = map(float, str_data_strip.split(" "))


