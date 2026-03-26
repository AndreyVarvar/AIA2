# JPEG compression
from src.dct import dct2d, idct2d
from src.rle import rle, irle
import numpy as np
import pygame as pg
pg.init()


def halve_matrix(matrix: list[list[int]]):
    halved = [[0]*(len(matrix[0])//2)]*(len(matrix)//2)

    for x in range(0, len(matrix[0])//2):
        for y in range(0, len(matrix)//2):
            halved[y][x] = matrix[y*2][x*2]
    
    return halved


def zigzag_scan(matrix):
    if not matrix or not matrix[0]:
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


def jpeg_dct(matrix: list[list[int]]):
    w = 8
    h = 8
    x_rem = len(matrix[0]) % w
    y_rem = len(matrix) % h

    for x in range(0, len(matrix[0]), 8):
        for y in range(0, len(matrix), 8):
            m = [[0]*w]*h
            for i in range(0, w if (x + 8 < len(matrix[0])) else x_rem):
                for j in range(0, h if (y + 8 < len(matrix)) else y_rem):
                    m[j][i] = matrix[y+j][x+i]
            m = dct2d(np.array(m))
            for i in range(0, w if (x + 8 < len(matrix[0])) else x_rem):
                for j in range(0, h if (y + 8 < len(matrix)) else y_rem):
                    matrix[y+j][x+i] = m[i][j]


def shave(matrix: list[list[float]], q_matrix: list[list[int]]):
    w = 8
    h = 8
    x_rem = len(matrix[0]) % w
    y_rem = len(matrix) % h

    for x in range(0, len(matrix[0]), 8):
        for y in range(0, len(matrix), 8):
            for i in range(0, w if (x + 8 < len(matrix[0])) else x_rem):
                for j in range(0, h if (y + 8 < len(matrix)) else y_rem):
                    matrix[y+j][x+i] /= q_matrix[j][i]


def compress(image: pg.Surface):  # https://cgjennings.ca/articles/jpeg-compression/
    # step 1: convert RGB image to YCbCr image
    # Y - Luma
    # Cb - Chroma Blue
    # Cr - Chroma Red

    luma = luma_from(image)
    chroma_blue = chroma_blue_from(image)
    chroma_red = chroma_red_from(image)

    # step 2: scale down Cb and Cr
    chroma_blue = halve_matrix(chroma_blue)  # scaling down by 0.5 will reduce the image to a quarter of it's original size
    chroma_red = halve_matrix(chroma_red)

    # step 3: convert to frequency domain (for each channel)
    jpeg_dct(luma)
    jpeg_dct(chroma_blue)
    jpeg_dct(chroma_red)

    # step 4: quantization matrix + shave
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

    shave(luma, luma_q_matrix)
    shave(chroma_blue, color_q_matrix)
    shave(chroma_red, color_q_matrix)



def luma_from(image: pg.Surface):
    luma = [[0]*image.width]*image.height

    for y in range(image.height):
        for x in range(image.width):
            pixel = image.get_at((x, y))
            r, g, b = pixel.r, pixel.g, pixel.b

            brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
            luma[y][x] = brightness
    
    return luma

def chroma_blue_from(image: pg.Surface):
    chroma_blue = [[0]*image.width]*image.height

    for y in range(image.height):
        for x in range(image.width):
            pixel = image.get_at((x, y))
            r, g, b = pixel.r, pixel.g, pixel.b

            intensity = -0.1687*r - 0.3313*g + 0.5*b + 128
            chroma_blue[y][x] = intensity
    
    return chroma_blue

def chroma_red_from(image: pg.Surface):
    chroma_red = [[0]*image.width]*image.height

    for y in range(image.height):
        for x in range(image.width):
            pixel = image.get_at((x, y))
            r, g, b = pixel.r, pixel.g, pixel.b

            intensity = 0.5*r - 0.4187*g - 0.0813*b + 128
            chroma_red[y][x] = intensity
    
    return chroma_red


display = pg.display.set_mode((800, 800))
image = pg.image.load("tests/to_compress.png")
compress(image)

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
    
    display.fill((255, 255, 255))

    display.blit(image, (100, 50))

    pg.display.update()

