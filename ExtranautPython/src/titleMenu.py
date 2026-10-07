import pygame
import constants
from titleMenuWindowManager import *
from spriteSheetManager import *
from animationSheetManager import *
from spriteSheet import *
from sheetSprite import *
import sounds
import webbrowser
class TitleMenu():
    def __init__(self, screen, messageOfTheDay):
        self.messageOfTheDay = messageOfTheDay
        self.titleMenuWindowManager = TitleMenuWindowManager(self.messageOfTheDay)
        self.gameOver = False
        pygame.mouse.set_visible(True)
        self.backgroundSprite = SheetSprite('titleTerrainSmall', [0, 0, 1024, 768])
        self.titleAnimation = AnimationSprite('extranautTitleAnimated', 0)
        self.kopaSprite = SheetSprite('kopa', [0, 0, 864, 32])
        self.mattSprite = SheetSprite('matt', [0, 0, 448, 32])
        
        self.animationTimeout = 60
        self.animationFrame = 0
        sounds.playMusic('ruinsCore', .3) 
        
    def handleEvent(self, event, mousePos, keys):
        if event.type == pygame.MOUSEBUTTONDOWN:
           if event.button == 1:
               val = self.titleMenuWindowManager.handleClick(mousePos)
               if not val == None:
                   return val
               else:
                   if mousePos[0] > 80 and mousePos[0] < 80 + 864 and mousePos[1] > 250 and mousePos[1] < 300+ 32:
                       try: 
                           webbrowser.open('http://kindofprettyalright.com/?fromExtranaut')
                       except webbrowser.Error:
                           print 'well we tried'
               
    def draw(self, screen):
        screen.blit(self.backgroundSprite.getImage(), (0,0))
        titleAnimationFrame = self.titleAnimation.getRectFrame([144*2, 64], self.animationFrame)
        scaledFrame = pygame.transform.scale(titleAnimationFrame, (titleAnimationFrame.get_width() * 2, titleAnimationFrame.get_height() * 2))
        screen.blit(scaledFrame, (250,50))
        screen.blit(self.kopaSprite.getImage(), (80, 250))
        screen.blit(self.mattSprite.getImage(), (300, 300))
        self.titleMenuWindowManager.draw(screen)
    
    def update(self, keys, mousePos, joystick, time):
        pygame.mouse.set_visible(True)
        self.animationTimeout -= time
        if self.animationTimeout <= 0:
            self.animationTimeout = 60
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
                
    