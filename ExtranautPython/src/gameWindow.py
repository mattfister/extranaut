import pygame
from pygame.rect import Rect
import constants
import spriteSheetManager
from spriteSheet import *
from sheetSprite import *
from animationSheet import *
from animationSprite import *
import math
import sounds

class GameWindow():
    def __init__(self, windowRect):
        self.windowRect = windowRect
        self.visible = True
        self.rectColor = [255, 255, 255]
        
    def collidesWith(self, pos):
        return self.windowRect.collidepoint(pos)
    
    def draw(self, screen):
        screen.fill((0,0,0), self.windowRect)
        pygame.draw.rect(screen, self.rectColor, self.windowRect, 1)

    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def isVisible(self):
        return self.visible
    
    def handleClick(self, pos):
        return False
    

class TileWindow(GameWindow):
    def __init__(self, tile, pos):
        self.tile = tile
        GameWindow.__init__(self, Rect((pos[0], pos[1], constants.tileSize+2, constants.tileSize+2)))
        self.visible = True
        self.rectColor = [255, 255, 0]
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        screen.blit(imageManager.images[self.tile.imageName], ((self.windowRect[0]+1, self.windowRect[1]+1)))
        
    def handleClick(self, pos):
        return self.tile
    
class SpriteSheetWindow(GameWindow):
    def __init__(self, spriteSheet, pos):
        GameWindow.__init__(self, Rect((pos[0], pos[1], spriteSheet.sheet.get_width() + 2, spriteSheet.sheet.get_height() + 2)))
        self.spriteSheet = spriteSheet
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        screen.blit(self.spriteSheet.sheet, ((self.windowRect[0] + 1, self.windowRect[1] + 1)))
    
    def handleClick(self, pos):
        windowPos = [pos[0] - self.windowRect[0], pos[1] - self.windowRect[1]]
        if windowPos[0] > self.spriteSheet.sheet.get_width():
            return []
        if windowPos[1] > self.spriteSheet.sheet.get_height():
            return []
        pos = [ int(math.fabs(math.floor((windowPos[0])/constants.tileSize))), int(math.fabs(math.floor((windowPos[1])/constants.tileSize)))]
        return SheetSprite(self.spriteSheet.name, [pos[0]*constants.tileSize, pos[1]*constants.tileSize, constants.tileSize, constants.tileSize])
  
class AnimationSheetWindow(GameWindow):
    def __init__(self, animationSheet, pos):
        GameWindow.__init__(self, Rect((pos[0], pos[1], animationSheet.sheet.get_width() + 2, animationSheet.sheet.get_height() + 2)))
        self.animationSheet = animationSheet
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        screen.blit(self.animationSheet.sheet, ((self.windowRect[0] + 1, self.windowRect[1] + 1)))
    
    def handleClick(self, pos):
        windowPos = [pos[0] - self.windowRect[0], pos[1] - self.windowRect[1]]
        if windowPos[0] > self.animationSheet.sheet.get_width():
            return []
        if windowPos[1] > self.animationSheet.sheet.get_height():
            return []
        pos = [ int(math.fabs(math.floor((windowPos[0])/constants.tileSize))), int(math.fabs(math.floor((windowPos[1])/constants.tileSize)))]
        return AnimationSprite(self.animationSheet.name, pos[1])
  
class MonsterWindow(GameWindow):
    def __init__(self, classList, pos):
        rect = pygame.Rect([pos[0], pos[1], constants.tileSize + 1, constants.tileSize + 1])
        GameWindow.__init__(self, rect)
        self.classList = classList
        self.index = 0
        
    def modulateMonster(self, amount):
        self.index += amount
        if self.index >= len(self.classList):
            self.index = 0
        elif self.index < 0:
            self.index = len(self.classList) - 1
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        
        monster = self.classList[self.index]((self.windowRect[0], self.windowRect[1]))
        monster.drawStatic(screen, [self.windowRect[0] + 16, self.windowRect[1] + 16])
        monster.shape.object = None
        monster.body = None
        monster.shape = None
        
    def handleClick(self, pos):
        return self.classList[self.index]
        
class ButtonWindow(GameWindow):
    def __init__(self, windowRect, text, onClickReturn):
        GameWindow.__init__(self, windowRect)
        self.visible = True
        self.text = text
        self.onClickReturn = onClickReturn
        self.rectColor = [255, 255, 255]
        
    def draw(self, screen):
        if self.visible:
            GameWindow.draw(self, screen)
            font = constants.defaultFont
            text = font.render(self.text, 0, (255, 255, 255))
            screen.blit(text, ((self.windowRect[0] + 3), self.windowRect[1])) # text.get_rect()[3]/2, self.windowRect[1]))
        
    def handleClick(self, pos):
        if self.visible:
            return self.onClickReturn

class SoundToggleButton(GameWindow):
    def __init__(self, windowRect):
        GameWindow.__init__(self, windowRect)
        self.offSprite = SheetSprite('options', [0, 0, 32, 32])
        self.onSprite = SheetSprite('options', [32, 0, 32, 32])
        self.soundOn = True
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        if self.soundOn:
            screen.blit(self.onSprite.getImage(), (self.windowRect[0]+1, self.windowRect[1]+1))
        else:
            screen.blit(self.offSprite.getImage(), (self.windowRect[0]+1, self.windowRect[1]+1))

    def handleClick(self, pos):
        if self.soundOn:
            self.soundOn = False
            constants.soundOverride = True
            sounds.stopMusic()
        else:
            self.soundOn = True
            constants.soundOverride = False
            sounds.playMusic('intro', .1) 

        return None

class FullScreenButton(GameWindow):
    def __init__(self, windowRect):
        GameWindow.__init__(self, windowRect)
        self.windowedSprite = SheetSprite('options', [0, 32, 32, 32])
        self.fullScreenSprite = SheetSprite('options', [32, 32, 32, 32])
        self.fullScreen = False
        
    def draw(self, screen):
        GameWindow.draw(self, screen)
        if self.fullScreen:
            screen.blit(self.fullScreenSprite.getImage(), (self.windowRect[0]+1, self.windowRect[1]+1))
        else:
            screen.blit(self.windowedSprite.getImage(), (self.windowRect[0]+1, self.windowRect[1]+1))

        
    def handleClick(self, pos):
        if self.fullScreen:
            self.fullScreen = False
            screen = pygame.display.set_mode([1024, 768], pygame.DOUBLEBUF|pygame.HWSURFACE|pygame.ASYNCBLIT, 32)
        else:
            self.fullScreen = True
            screen = pygame.display.set_mode([1024, 768], pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.HWSURFACE|pygame.ASYNCBLIT, 32)
            
        return None
    
    

class TextWindow(GameWindow):
    def __init__(self, windowRect, text):
        GameWindow.__init__(self, windowRect)
        self.visible = True
        self.text = text
    
    def draw(self, screen):
        font = constants.defaultFont
        text = font.render(self.text, 0, (255, 255, 255))
        screen.blit(text, ((self.windowRect[0] + 3), self.windowRect[1]))
