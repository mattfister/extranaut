from gameWindow import *
import spriteSheetManager
import animationSheetManager
import pygame
import constants
from monster import *

class MapEditorWindowManager():
    def __init__(self, curLayer): #initialization for map editor
        tileList = []
        self.windows = []
        
        self.curSpriteSheetIndex = 0
        self.curAnimationSheetIndex = 0
        
        self.spriteSheetWindow = None
        self.animationSheetWindow = None
        
        self.updateSpriteSheetIndex(0)
        self.updateAnimationSheetIndex(0)
        
        self.prevSpriteButton = ButtonWindow(pygame.Rect(0, constants.resolution[1]-270, 128, 13), 'Previous', constants.prevSpriteSheet)
        self.nextSpriteButton = ButtonWindow(pygame.Rect(129, constants.resolution[1]-270, 128, 13), 'Next', constants.nextSpriteSheet)
        
        self.prevAnimationButton = ButtonWindow(pygame.Rect(0, constants.resolution[1]-626, 128, 13), 'Previous', constants.nextAnimationSheet)
        self.nextAnimationButton = ButtonWindow(pygame.Rect(129, constants.resolution[1]-626, 128, 13), 'Next', constants.nextAnimationSheet)
        self.undoAnimationButton = ButtonWindow(pygame.Rect(257, constants.resolution[1]-626, 50, 13), 'Undo', constants.popAnimation)
        self.windows.append(self.undoAnimationButton)
        
        self.backGroundLayerButton = ButtonWindow(pygame.Rect(100, 0, 100, 13), 'background', constants.backgroundLayer)
        self.midGroundLayerButton = ButtonWindow(pygame.Rect(200, 0, 100, 13), 'midground', constants.midgroundLayer)
        self.foreGroundLayerButton = ButtonWindow(pygame.Rect(300, 0, 100, 13), 'foreground', constants.foregroundLayer)
        
        self.backGroundVisibiltyButton = ButtonWindow(pygame.Rect(100, 13, 100, 13), 'visible', constants.toggleBackgroundVisibility)
        self.windows.append(self.backGroundVisibiltyButton)
        
        self.midGroundVisibilityButton = ButtonWindow(pygame.Rect(200, 13, 100, 13), 'visibile', constants.toggleMidgroundVisibility)
        self.windows.append(self.midGroundVisibilityButton)
        
        self.foreGroundVisibilityButton = ButtonWindow(pygame.Rect(300, 13, 100, 13), 'visible', constants.toggleForegroundVisibility)
        self.windows.append(self.foreGroundVisibilityButton)
        
        self.fillButton = ButtonWindow(pygame.Rect(270, constants.resolution[1]-13, 30, 13), 'fill', constants.fillLayer)
        self.windows.append(self.fillButton)
        
        self.fpsWindow = TextWindow(pygame.Rect(0,0, 50, 13), 0)
        self.windows.append(self.fpsWindow)
        
        self.wallButton = ButtonWindow(pygame.Rect(0, constants.resolution[1]-300, 50, 32), 'Wall', constants.buildWall)
        self.windows.append(self.wallButton)
        self.undoWallButton = ButtonWindow(pygame.Rect(50, constants.resolution[1]-300, 50, 32), 'Undo', constants.popWall)
        self.windows.append(self.undoWallButton)
        
        self.startButton = ButtonWindow(pygame.Rect(constants.resolution[0] - 120, 0, 60, 13), 'Start', constants.startSimulation)
        self.windows.append(self.startButton)
        
        self.stopButton = ButtonWindow(pygame.Rect(constants.resolution[0] - 60, 0, 60, 13), 'Stop', constants.stopSimulation)
        self.windows.append(self.stopButton)
        
        self.musicButton = ButtonWindow(pygame.Rect(constants.resolution[0]-60, 13, 60, 13), 'Music', constants.setMusic)
        self.windows.append(self.musicButton)
        
        self.setCurLayer(curLayer)
        
        self.monsterClassList = []
        self.monsterClassList.append(BallMonster)
        self.monsterClassList.append(SpikyBallMonster)
        self.monsterClassList.append(DefenseTurretVertical)
        self.monsterClassList.append(Flyer)
        self.monsterClassList.append(Beast)
        self.monsterClassList.append(FlyBot)
        self.monsterClassList.append(SavePoint)
        self.monsterClassList.append(HpPowerup)
        self.monsterClassList.append(AlienArtifact)
        self.monsterClassList.append(GunPowerup)
        self.monsterClassList.append(FuelPowerup)
        self.monsterClassList.append(ArtifactDoor)
        self.monsterClassList.append(MonsterDoor)
        self.monsterClassList.append(MonsterDoor2)
        self.monsterClassList.append(HoverBlock)
        self.monsterClassList.append(BossBot1)
        self.monsterClassList.append(BossBot2)
        self.monsterClassList.append(BossBot3)
        self.monsterClassList.append(HandBot)
        self.monsterClassList.append(OrbBoss)
        self.monsterClassList.append(JumpBot)
        self.monsterClassList.append(AimerTurret)
        self.monsterClassList.append(OctoBoss)
        self.monsterClassList.append(HeadBoss)
        self.monsterClassList.append(SpikyHeadMonster)
        self.monsterClassList.append(FallenExtranaut)
        
        self.monsterWindow = MonsterWindow(self.monsterClassList, [1, 53])
        
        self.prevMonsterButton = ButtonWindow(pygame.Rect(0, 40, 50, 13), 'Prev', constants.prevMonster)
        self.nextMonsterButton = ButtonWindow(pygame.Rect(50, 40, 50, 13), 'Next', constants.nextMonster)
        self.undoMonsterButton = ButtonWindow(pygame.Rect(100, 40, 50, 13), 'Undo', constants.popMonster)
        self.windows.append(self.undoMonsterButton)
        
        self.saveButton = ButtonWindow(pygame.Rect( 500, 0, 50, 13), 'Save', constants.saveWorld)
        self.windows.append(self.saveButton)
        self.loadButton = ButtonWindow(pygame.Rect( 600, 0, 50, 13), 'Load', constants.loadWorld)
        self.windows.append(self.loadButton)
        
        self.roomUpButton = ButtonWindow(pygame.Rect(700, 0, 50, 13), 'Up', constants.roomUp)
        self.windows.append(self.roomUpButton)
        
        self.roomDownButton = ButtonWindow(pygame.Rect(750, 0, 50, 13), 'Down', constants.roomDown)
        self.windows.append(self.roomDownButton)
        
        self.roomLeftButton = ButtonWindow(pygame.Rect(800, 0, 50, 13), 'Left', constants.roomLeft)
        self.windows.append(self.roomLeftButton)
        
        self.roomRightButton = ButtonWindow(pygame.Rect(850, 0, 50, 13), 'Right', constants.roomRight)
        self.windows.append(self.roomRightButton)
        
        self.playerPositionButton = ButtonWindow(pygame.Rect(0, constants.resolution[1] - 350, 50, 13), 'Player', constants.playerPosition)
        self.windows.append(self.playerPositionButton)
        
        
    def updateFpsWindow(self, fps):
        self.fpsWindow.text = str(fps)
        
    def defaultWindows(self):
        pass
    
    def setCurLayer(self, curLayer):
        if curLayer == 'background':
            self.backGroundLayerButton.rectColor = [255, 0, 0]
            self.midGroundLayerButton.rectColor = [255, 255, 0]
            self.foreGroundLayerButton.rectColor = [255, 255, 0]
        elif curLayer == 'midground':
            self.backGroundLayerButton.rectColor = [255, 255, 0]
            self.midGroundLayerButton.rectColor = [255, 0, 0]
            self.foreGroundLayerButton.rectColor = [255, 255, 0]
        elif curLayer == 'foreground':
            self.backGroundLayerButton.rectColor = [255, 255, 0]
            self.midGroundLayerButton.rectColor = [255, 255, 0]
            self.foreGroundLayerButton.rectColor = [255, 0, 0]
            
    def draw(self, screen, camera):
        self.spriteSheetWindow.draw(screen)
        self.prevSpriteButton.draw(screen)
        self.nextSpriteButton.draw(screen)
        self.prevAnimationButton.draw(screen)
        self.nextAnimationButton.draw(screen)
        self.animationSheetWindow.draw(screen)
        self.backGroundLayerButton.draw(screen)
        self.midGroundLayerButton.draw(screen)
        self.foreGroundLayerButton.draw(screen)
        self.monsterWindow.draw(screen)
        self.prevMonsterButton.draw(screen)
        self.nextMonsterButton.draw(screen)
        
        for window in self.windows:
            window.draw(screen)
            
    def updateSpriteSheetIndex(self, offset):
        self.curSpriteSheetIndex += offset
        if self.curSpriteSheetIndex < 0:
            self.curSpriteSheetIndex = len(spriteSheetManager.spriteSheets.values()) - 1
        elif self.curSpriteSheetIndex >= len(spriteSheetManager.spriteSheets.values()):
            self.curSpriteSheetIndex = 0
        
        curSpriteSheet = spriteSheetManager.spriteSheets.values()[self.curSpriteSheetIndex]
        self.spriteSheetWindow = SpriteSheetWindow(curSpriteSheet, [0, constants.resolution[1]-256])
    
    def updateAnimationSheetIndex(self, offset):
        self.curAnimationSheetIndex += offset
        if self.curAnimationSheetIndex < 0:
            self.curAnimationSheetIndex = len(animationSheetManager.animationSheets.values()) - 1
        elif self.curAnimationSheetIndex >= len(animationSheetManager.animationSheets.values()):
            self.curAnimationSheetIndex = 0
        
        curAnimationSheet = animationSheetManager.animationSheets.values()[self.curAnimationSheetIndex]
        self.animationSheetWindow = AnimationSheetWindow(curAnimationSheet, [0, constants.resolution[1] - 612])
        
    def handleClick(self, mousePos):
        for window in self.windows:
            if window.collidesWith(mousePos):
                return window.handleClick(mousePos)
        if self.spriteSheetWindow.collidesWith(mousePos):
            return self.spriteSheetWindow.handleClick(mousePos)
        elif self.animationSheetWindow.collidesWith(mousePos):
            return self.animationSheetWindow.handleClick(mousePos)
        elif self.prevSpriteButton.collidesWith(mousePos):
            self.updateSpriteSheetIndex(-1)
            return constants.prevSpriteSheet
        elif self.nextSpriteButton.collidesWith(mousePos):
            self.updateSpriteSheetIndex(1)
            return constants.nextSpriteSheet
        elif self.prevAnimationButton.collidesWith(mousePos):
            self.updateAnimationSheetIndex(-1)
            return constants.prevAnimationSheet
        elif self.nextAnimationButton.collidesWith(mousePos):
            self.updateAnimationSheetIndex(1)
            return constants.nextAnimationSheet
        elif self.prevMonsterButton.collidesWith(mousePos):
            self.monsterWindow.modulateMonster(-1)
            return constants.prevMonster
        elif self.nextMonsterButton.collidesWith(mousePos):
            self.monsterWindow.modulateMonster(1)
            return constants.nextMonster
        elif self.foreGroundLayerButton.collidesWith(mousePos):
            return self.foreGroundLayerButton.handleClick(mousePos)
        elif self.midGroundLayerButton.collidesWith(mousePos):
            return self.midGroundLayerButton.handleClick(mousePos)
        elif self.backGroundLayerButton.collidesWith(mousePos):
            return self.backGroundLayerButton.handleClick(mousePos)
        elif self.monsterWindow.collidesWith(mousePos):
            return self.monsterWindow.handleClick(mousePos)
        return None