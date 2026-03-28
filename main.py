import pygame as pg
from src.jpeg import jpeg, ijpeg

display = pg.display.set_mode((800, 800))
jpeg(image_path="tests/to_compress.png")
ijpeg("results/to_compress.jpeg")

running = False
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
    
    display.fill((255, 255, 255))

    display.blit(image, (100, 50))

    pg.display.update()

