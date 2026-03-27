import pygame as pg
from src.jpeg import jpeg_compress_2
import src.jpeg

display = pg.display.set_mode((800, 800))
image = pg.image.load("tests/to_compress.png")
jpeg_compress_2(image)

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
    
    display.fill((255, 255, 255))

    display.blit(image, (100, 50))

    pg.display.update()

