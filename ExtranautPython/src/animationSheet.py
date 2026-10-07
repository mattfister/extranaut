import pygame
import constants
import copy

class AnimationSheet():
    def __init__(self, sheet, name):
        self.sheet = sheet
        self.name = name
        
    def getImageAtRect(self, fromRect):
        rect = pygame.Rect(fromRect)
        image = pygame.Surface((rect.size), pygame.SRCALPHA, 32);
        image.blit(self.sheet, (0,0), rect)
        return image
    
    def getNumFrames(self):
        return self.sheet.get_width() / constants.tileSize
    
    def getFrame(self, rowNum, frameNum):
        rect = pygame.Rect(frameNum * constants.tileSize, rowNum * constants.tileSize, constants.tileSize, constants.tileSize)
        return self.getImageAtRect(rect)
