import animationSheetManager
import animationSheet
import pygame

class AnimationSprite():
    def __init__(self, animationSheetName, row):
        self.animationSheetName = animationSheetName
        self.row = row
        
    def getFrame(self, frame):
        return animationSheetManager.animationSheets[self.animationSheetName].getFrame(self.row, frame)
    
    def getNumFrames(self):
        return animationSheetManager.animationSheets[self.animationSheetName].getNumFrames()
    
    def getSizedFrame(self, rectSize, frame):
        xPos = frame * rectSize
        yPos = self.row * rectSize
        rect = pygame.Rect([xPos, yPos, rectSize, rectSize])
        return animationSheetManager.animationSheets[self.animationSheetName].getImageAtRect(rect)
    
    def getRectFrame(self, rect, frame):
        xPos = frame * rect[0]
        yPos = self.row * rect[1]
        rect = pygame.Rect([xPos, yPos, rect[0], rect[1]])
        return animationSheetManager.animationSheets[self.animationSheetName].getImageAtRect(rect)