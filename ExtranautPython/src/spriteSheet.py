import pygame
import constants
import copy

class SpriteSheet():
    def __init__(self, sheet, name):
        self.sheet = sheet
        self.name = name
        
    def getImageAtRect(self, fromRect):
        rect = pygame.Rect(fromRect)
        image = pygame.Surface((rect.size), pygame.SRCALPHA, 32);
        image.blit(self.sheet, (0,0), rect)
        return image
    
    def getImage(self, coords):
        rect = pygame.Rect(coords[0], coords[1], constants.tileSize, constants.tileSize)
        return self.getImageAtRect(rect)
