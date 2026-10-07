from gameWindow import *
from constants import *
import pygame

class PauseMenuWindowManager():
    def __init__(self): #initialization for game editor
        self.windows = []
        self.setupWindows()
    
    def setupWindows(self):
        self.windows = []
        
        buttonLength = 120
        buttonHeight = 20
        buttonLength2 = 220
        
        self.windows.append(ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength/2, constants.resolution[1]/2 - 0*buttonHeight, buttonLength, buttonHeight]), "Quit to Title", constants.quitToTitleReturn))
        self.windows.append(ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength/2, constants.resolution[1]/2 + 3*buttonHeight, buttonLength, buttonHeight]), "Quit Game", constants.quitToDesktopReturn))
        self.windows.append(ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength/2, constants.resolution[1]/2 + 6*buttonHeight, buttonLength, buttonHeight]), "Resume Game", constants.resumeGame))
    
    def defaultWindows(self):
        pass
    
    def draw(self, screen):
        for window in self.windows:
            window.draw(screen) 
        
    def handleClick(self, mousePos):
        for window in self.windows:
            if window.collidesWith(mousePos):
                return window.handleClick(mousePos)
        return None
