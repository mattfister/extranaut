from gameWindow import *
from constants import *
import pygame
class TitleMenuWindowManager():
    def __init__(self, messageOfTheDay): 
        self.messageOfTheDay = messageOfTheDay
        print 'messageOfTheday = ' + str(messageOfTheDay)
        self.windows = []
        self.setupWindows()
    
    def setupWindows(self):
        self.windows = []
        # OK Need to see what save files exist        
        file1 = None
        file2 = None
        file3 = None
        try:
            file1 = open('../saves/1/save.xns', 'rb')
        except IOError:
            print 'file 1 not present'
        
        try:
            file2 = open('../saves/2/save.xns', 'rb')
        except IOError:
            print 'file2 not present'
            
        try:
            file3 = open('../saves/3/save.xns', 'rb')
        except IOError:
            print 'file3 not present'
            
        if file1 != None:
            file1.close()
        if file2 != None:
            file2.close()
        if file3 != None:
            file3.close()
            
        buttonLength = 140
        buttonHeight = 20
        buttonLength2 = 240
        
        if file1 == None:
            self.newGameButton1 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 100, constants.resolution[1]/2 - 0*buttonHeight, buttonLength2, buttonHeight]), "New Game 1 - Planet Zorta", constants.titleMenuNewGameZorta1)
            self.windows.append(self.newGameButton1)
            self.newGameCustomButton1 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 + 25, constants.resolution[1]/2 - 0*buttonHeight, buttonLength2, buttonHeight]), "New Game 1 - Custom Planet", constants.titleMenuNewCustom1)
            self.windows.append(self.newGameCustomButton1)
        else:
            self.loadGameButton1 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 25, constants.resolution[1]/2 - 0*buttonHeight, buttonLength, buttonHeight]), "Load Game 1", constants.titleMenuLoadGame1)
            self.windows.append(self.loadGameButton1)
            self.deleteGameButton1 = ButtonWindow(pygame.Rect([constants.resolution[0]/2  + 25, constants.resolution[1]/2 - 0*buttonHeight, buttonLength, buttonHeight]), "Delete Game 1", constants.titleMenuDeleteGame1)
            self.windows.append(self.deleteGameButton1)
            
        if file2 == None:
            self.newGameButton2 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 100, constants.resolution[1]/2 + 3*buttonHeight, buttonLength2, buttonHeight]), "New Game 2 - Planet Zorta", constants.titleMenuNewGameZorta2)
            self.windows.append(self.newGameButton2)
            self.newGameCustomButton2 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 + 25, constants.resolution[1]/2 + 3*buttonHeight, buttonLength2, buttonHeight]), "New Game 2 - Custom Planet", constants.titleMenuNewCustom2)
            self.windows.append(self.newGameCustomButton2)
        else:
            self.loadGameButton2 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 25, constants.resolution[1]/2 + 3*buttonHeight, buttonLength, buttonHeight]), "Load Game 2", constants.titleMenuLoadGame2)
            self.windows.append(self.loadGameButton2)
            self.deleteGameButton2 = ButtonWindow(pygame.Rect([constants.resolution[0]/2  + 25, constants.resolution[1]/2 + 3*buttonHeight, buttonLength, buttonHeight]), "Delete Game 2", constants.titleMenuDeleteGame2)
            self.windows.append(self.deleteGameButton2)
        
        if file3 == None:
            self.newGameButton3 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 100, constants.resolution[1]/2 + 6*buttonHeight, buttonLength2, buttonHeight]), "New Game 3 - Planet Zorta", constants.titleMenuNewGameZorta3)
            self.windows.append(self.newGameButton3)
            self.newGameCustomButton3 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 + 25, constants.resolution[1]/2 + 6*buttonHeight, buttonLength2, buttonHeight]), "New Game 3 - Custom Planet", constants.titleMenuNewCustom3)
            self.windows.append(self.newGameCustomButton3)
        else:
            self.loadGameButton3 = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength - 25, constants.resolution[1]/2 + 6*buttonHeight, buttonLength, buttonHeight]), "Load Game 3", constants.titleMenuLoadGame3)
            self.windows.append(self.loadGameButton3)
            self.deleteGameButton3 = ButtonWindow(pygame.Rect([constants.resolution[0]/2  + 25, constants.resolution[1]/2 + 6*buttonHeight, buttonLength, buttonHeight]), "Delete Game 3", constants.titleMenuDeleteGame3)
            self.windows.append(self.deleteGameButton3)
        
        self.chaosnautButton = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength/2, constants.resolution[1]/2 + 9*buttonHeight, buttonLength, buttonHeight]), "Chaosnaut", constants.chaosnautReturn)
        self.windows.append(self.chaosnautButton)
        self.mapEditorButton = ButtonWindow(pygame.Rect([constants.resolution[0]/2 - buttonLength/2, constants.resolution[1]/2 +12*buttonHeight, buttonLength, buttonHeight]), "Map Editor", constants.titleMenuMapEditorReturn)
        self.windows.append(self.mapEditorButton)
        self.soundButton = SoundToggleButton(pygame.Rect([0, constants.resolution[1] - 34, 34, 34]))
        self.windows.append(self.soundButton)
        self.fullScreenButton = FullScreenButton(pygame.Rect([33, constants.resolution[1] - 34, 34, 34]))
        self.windows.append(self.fullScreenButton)
        
        self.windows.append(TextWindow(pygame.Rect([constants.resolution[0]/2 - 400, constants.resolution[1]-40, buttonLength, buttonHeight]), 'Version 1.0'))
        
        if self.messageOfTheDay != None:
            self.windows.append(TextWindow(pygame.Rect([constants.resolution[0]/2 - 400, constants.resolution[1]-20, buttonLength, buttonHeight]), self.messageOfTheDay))
            
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
