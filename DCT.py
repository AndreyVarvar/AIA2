from math import cos, pi

def DCT(matrix: list[list[int]], h: int, w: int):
    n = h
    m = w
    dct_matrix = [[0]*m]*n  # makes  n x m  matrix
    for u in range(0, n):
        for v in range(0, m):
            dct_matrix[u][v] = 0
            for i in range(0, n):
                for j in range(0, m):
                    dct_matrix[u][v] += matrix[i][j] * cos(pi/n * (i+0.5) * u) * cos(pi/m * (j+0.5) * v)
    return dct_matrix
