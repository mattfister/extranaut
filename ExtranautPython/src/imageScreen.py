import pygame
from sheetSprite import *

class ImageScreen():
    def __init__(self, imageName, returnVal):
        self.imageName = imageName
        self.image = SheetSprite(self.imageName, [0, 0, 1024, 768])
        self.returnVal = returnVal
        self.gameOver = False
        
    def update(self, keys, mousePos, joystick, time):
        pass
    
    def draw(self, screen):
        screen.blit(self.image.getImage(), (0,0))
        
    def handleEvent(self, event, mousepos, keys):
        if event.type == pygame.KEYDOWN:
            return self.returnVal
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.returnVal
        if event.type == pygame.JOYBUTTONDOWN:
            return self.returnVal