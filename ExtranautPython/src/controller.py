import pygame
import pygame.mouse
from titleMenu import *
from xenoCartographer import *
from game import *
from chaosnaut import *
import sounds
import wx
import shutil
import gc
from imageScreen import *

class Controller():
    def __init__(self, screen, messageOfTheDay):
        self.messageOfTheDay = messageOfTheDay
        self.titleMenu = TitleMenu(screen, messageOfTheDay)
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = self.titleMenu
        self.nextState = None
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        self.application = wx.PySimpleApp()
        
    def drawScene(self, screen):
        self.screen.fill((0, 0, 0))
        self.state.draw(self.screen);
        pygame.display.flip()
    
    def gameLoop(self):
        while(1):
            mousePos = pygame.mouse.get_pos()
            keys=pygame.key.get_pressed()
            val = 0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    raise SystemExit()
                else:
                    val = self.state.handleEvent(e, mousePos, keys)
                    
            if self.state == self.titleMenu:
                if val == constants.titleMenuMapEditorReturn:
                    self.state = XenoCartographer(self.screen, 'mapName')
                    
                if val == constants.titleMenuNewGameZorta1:
                    shutil.copy('../data/zorta.xn0', '../saves/1/save.xns')
                    self.nextState = Game(self.screen, '../saves/1/save.xns', 1)
                    self.state = ImageScreen('intro', constants.introScreenReturn)
                if val == constants.titleMenuDeleteGame1:
                    os.remove('../saves/1/save.xns')
                    self.state.titleMenuWindowManager.setupWindows() 
                if val == constants.titleMenuLoadGame1:
                    self.state = Game(self.screen, '../saves/1/save.xns', 1)
                if val == constants.titleMenuNewCustom1:
                    dialog = wx.FileDialog( None, style = wx.FD_OPEN )
                    file_path = None
                    if dialog.ShowModal() == wx.ID_OK:
                        file_path = dialog.GetPath()
                    else:
                        print 'Nothing was selected'
                    dialog.Destroy()
                    if file_path != None:
                        shutil.copy(file_path, '../saves/1/save.xns')
                        self.state = Game(self.screen, '../saves/1/save.xns', 3)

                if val == constants.titleMenuNewGameZorta2:
                    shutil.copy('../data/zorta.xn0', '../saves/2/save.xns')
                    self.nextState = Game(self.screen, '../saves/2/save.xns', 2)
                    self.state = ImageScreen('intro', constants.introScreenReturn)
                    
                if val == constants.titleMenuDeleteGame2:
                    os.remove('../saves/2/save.xns')
                    self.state.titleMenuWindowManager.setupWindows()
                if val == constants.titleMenuLoadGame2:
                    self.state = Game(self.screen, '../saves/2/save.xns', 2)
                if val == constants.titleMenuNewCustom2:
                    dialog = wx.FileDialog( None, style = wx.FD_OPEN )
                    file_path = None
                    if dialog.ShowModal() == wx.ID_OK:
                        file_path = dialog.GetPath()
                    else:
                        print 'Nothing was selected'
                    dialog.Destroy()
                    if file_path != None:
                        shutil.copy(file_path, '../saves/2/save.xns')
                        self.state = Game(self.screen, '../saves/2/save.xns', 3)

                if val == constants.titleMenuNewGameZorta3:
                    shutil.copy('../data/zorta.xn0', '../saves/3/save.xns')
                    self.nextState = Game(self.screen, '../saves/2/save.xns', 2)
                    self.state = ImageScreen('intro', constants.introScreenReturn)
                if val == constants.titleMenuDeleteGame3:
                    os.remove('../saves/3/save.xns')
                    self.state.titleMenuWindowManager.setupWindows()
                if val == constants.titleMenuLoadGame3:
                    self.state = Game(self.screen, '../saves/3/save.xns', 3)
                if val == constants.titleMenuNewCustom3:
                    dialog = wx.FileDialog( None, style = wx.FD_OPEN )
                    file_path = None
                    if dialog.ShowModal() == wx.ID_OK:
                        file_path = dialog.GetPath()
                    else:
                        print 'Nothing was selected'
                    dialog.Destroy()
                    if file_path != None:
                        shutil.copy(file_path, '..saves/3/save.xns')
                        self.state = Game(self.screen, '../saves/3/save.xns', 3)

                if val == constants.chaosnautReturn:
                    self.state = Chaosnaut(self.screen)
                
            if val == constants.introScreenReturn:
                self.state = self.nextState
                self.nextState = None
            
            if val == constants.endingScreenReturn:
                self.state.gameOver = True
                    
            if val == constants.lostGame:
                self.state.gameOver = True
            
            
            
            if val == constants.quitToTitleReturn:
                self.state.gameOver = True
            
            time = self.clock.tick(60)
            
            returnVal = self.state.update(keys, mousePos, self.joystick, time)
            sounds.sound_manager.update(time)
            self.drawScene(self.screen)
            
            if returnVal == constants.wonGameReturn:
                self.state = ImageScreen('ending', constants.endingScreenReturn)
                
            
            
            if returnVal == constants.chasonautGameOver:
                waveNumber = self.state.curRoom.waveNumber
                enemiesKilled = self.state.curRoom.enemiesKilled
                self.state.gameOver = True
            
            if self.state.gameOver == True:
                self.state = self.titleMenu
                self.state.titleMenuWindowManager.setupWindows()