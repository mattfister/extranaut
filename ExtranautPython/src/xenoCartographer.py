import constants
import pygame
import cPickle
from pygame import Rect
from mapEditorWindowManager import *
from animationSprite import *
import copy
from planet import *
from tile import *
import pymunk
from monster import *
import wx

class XenoCartographer():
   def __init__( self, screen, name ):
       self.camera = [0.0,0.0]
       self.gameOver = False
       
       self.brush = None
       self.planet = Planet()
       self.roomCursorX = 0
       self.roomCursorY = 0
       self.curRoom = self.planet.rooms[self.roomCursorX][self.roomCursorY]
       self.curLayer = 'midground'
       self.windowManager = MapEditorWindowManager(self.curLayer)
       
       self.drawing = False
       self.wallPoints = []
       self.backgroundVisible = True
       self.midgroundVisible = True
       self.foregroundVisible = True
       
       self.application = wx.PySimpleApp()
       
   def modulateRoom(self, xChange, yChange):
       self.roomCursorX += xChange
       self.roomCursorY += yChange
       if self.roomCursorX < 0:
           self.roomCursorX = 0
       if self.roomCursorX > constants.numRoomsX - 1:
           self.roomCursorX = constants.numRoomsX - 1
       if self.roomCursorY < 0:
           self.roomCursorY = 0
       if self.roomCursorY > constants.numRoomsY - 1:
           self.roomCursorY = constants.numRoomsY - 1
       print self.roomCursorX
       print self.roomCursorY
       self.curRoom = self.planet.rooms[self.roomCursorX][self.roomCursorY]
       
   def savePlanet(self):
       if self.curRoom.simulation == False:
           dialog = wx.FileDialog( None, style = wx.FD_SAVE )
           file_path = None
           if dialog.ShowModal() == wx.ID_OK:
               file_path = dialog.GetPath()
           else:
               print 'Nothing was selected.'

           dialog.Destroy()
               
           if file_path != None:
               saveFile = open(file_path, 'wb')
               savePlanet = copy.copy(self.planet)
               for roomRow in savePlanet.rooms:
                   for room in roomRow:
                       room.prepForPickling()
               
               cPickle.dump(savePlanet, saveFile)
               saveFile.close()
               for roomRow in savePlanet.rooms:
                   for room in roomRow:
                       room.prepFromUnpickling()
               self.curRoom = self.planet.rooms[0][0]
       
   def loadPlanet(self):
       if self.curRoom.simulation == False:
           dialog = wx.FileDialog( None, style = wx.FD_OPEN )
           file_path = None
           if dialog.ShowModal() == wx.ID_OK:
               file_path = dialog.GetPath()
           else:
               print 'Nothing was selected'
           dialog.Destroy()
           if file_path != None:
               loadFile = open(file_path, 'rb')
               self.planet = cPickle.load(loadFile)
               loadFile.close()
               for roomRow in self.planet.rooms:
                   for room in roomRow:
                       room.prepFromUnpickling()
               self.roomCursorX = 0
               self.roomCursorY = 0
               self.curRoom = self.planet.rooms[0][0]
   
   def setMusic(self):
      if self.curRoom.simulation == False:
           dialog = wx.FileDialog( None, style = wx.FD_OPEN )
           fileName = None
           if dialog.ShowModal() == wx.ID_OK:
               fileName = dialog.GetFilename()
           else:
               print 'Nothing was selected'
           dialog.Destroy()
           if fileName != None:
               [name, sep, junk] = fileName.partition('.')
               self.curRoom.music = name
               print 'set music to ' + self.curRoom.music

   def draw(self, screen):
       self.curRoom.draw(screen, self.camera, self.backgroundVisible, self.midgroundVisible, self.foregroundVisible)
       
       roomAbove = None
       roomBelow = None
       roomLeft = None
       roomRight = None
       if self.roomCursorY > 0:
           roomAbove = self.planet.rooms[self.roomCursorX][self.roomCursorY - 1]
       if self.roomCursorY < constants.numRoomsY - 1:
           roomBelow = self.planet.rooms[self.roomCursorX][self.roomCursorY + 1]
       if self.roomCursorX > 0:
           roomLeft = self.planet.rooms[self.roomCursorX - 1][self.roomCursorY]
       if self.roomCursorX < constants.numRoomsX - 1:
           roomRight = self.planet.rooms[self.roomCursorX + 1][self.roomCursorY]
           
       if roomAbove != None:
           roomAbove.draw(screen, [self.camera[0], self.camera[1] - constants.roomSizeY * constants.tileSize])
       if roomBelow != None:
           roomBelow.draw(screen, [self.camera[0], self.camera[1] + constants.roomSizeY * constants.tileSize])
       if roomLeft != None:
           roomLeft.draw(screen, [self.camera[0] - constants.roomSizeX * constants.tileSize, self.camera[1]])
       if roomRight != None:
           roomRight.draw(screen, [self.camera[0] + constants.roomSizeX * constants.tileSize, self.camera[1]])
           
       self.windowManager.draw(screen, self.camera)
       self.curRoom.drawWalls(screen, self.camera)
       
   def handleEvent(self, event, mousepos, keys):
       if event.type == pygame.MOUSEBUTTONDOWN:
           if event.button == 1:
               newBrush = copy.copy(self.windowManager.handleClick(mousepos))
               if newBrush == constants.backgroundLayer:
                   self.curLayer = 'background'
                   self.windowManager.setCurLayer('background')
                   self.drawing = False
               elif newBrush == constants.midgroundLayer:
                   self.curLayer = 'midground'
                   self.windowManager.setCurLayer('midground')
                   self.drawing = False
               elif newBrush == constants.foregroundLayer:
                   self.curLayer = 'foreground'
                   self.windowManager.setCurLayer('foreground')
                   self.drawing = False
               elif newBrush == constants.fillLayer:
                   for x in range(0, constants.roomSizeX):
                       for y in range(0, constants.roomSizeY):
                          newTile = Tile(copy.copy(self.brush), [x * constants.tileSize, y * constants.tileSize])
                          self.curRoom.addTile(self.curLayer, newTile)
                          self.drawing = False
               elif newBrush == constants.buildWall:
                   self.brush = constants.buildWall
                   self.drawing = False
               elif newBrush == constants.startSimulation:
                   self.curRoom.startPhysicsSimulation()
                   self.drawing = False
               elif newBrush == constants.stopSimulation:
                   self.curRoom.stopPhysicsSimulation()
                   self.drawing = False
               elif newBrush == constants.setMusic:
                   self.setMusic()
                   self.drawing = False
               elif newBrush == constants.saveWorld:
                   self.savePlanet()
                   self.drawing = False
               elif newBrush == constants.loadWorld:
                   self.loadPlanet()
                   self.drawing = False
               elif isinstance(newBrush, SheetSprite):
                   self.brush = newBrush
                   self.drawing = False
               elif isinstance(newBrush, AnimationSprite):
                   self.brush = newBrush
                   self.drawing = False
               elif newBrush in self.windowManager.monsterClassList:
                   self.brush = newBrush
                   self.drawing = False
               elif newBrush == constants.popAnimation:
                   self.curRoom.popAnimation(self.curLayer)
                   self.drawing = False
               elif newBrush == constants.popMonster:
                   self.curRoom.popMonster()
                   self.drawing = False
               elif newBrush == constants.popWall:
                   self.curRoom.popWall()
                   self.drawing = False
               elif newBrush == constants.roomUp:
                   self.modulateRoom(0, -1)
                   self.drawing = False
               elif newBrush == constants.roomDown:
                   self.modulateRoom(0, 1)
                   self.drawing = False
               elif newBrush == constants.roomLeft:
                   self.modulateRoom(-1, 0)
                   self.drawing = False
               elif newBrush == constants.roomRight:
                   self.modulateRoom(1, 0)
                   self.drawing = False
               elif newBrush == constants.playerPosition:
                   self.brush = newBrush
                   self.drawing = False
               elif newBrush == constants.toggleBackgroundVisibility:
                   self.curRoom.needRebuffer = True
                   self.curRoom.allDirty = True
                   self.drawing = False
                   if self.backgroundVisible == True:
                       self.backgroundVisible = False
                   else:
                       self.backgroundVisible = True
               elif newBrush == constants.toggleMidgroundVisibility:
                   self.curRoom.needRebuffer = True
                   self.curRoom.allDirty = True
                   self.drawing = False
                   if self.midgroundVisible == True:
                       self.midgroundVisible = False
                   else:
                       self.midgroundVisible = True
               elif newBrush == constants.toggleForegroundVisibility:
                   self.curRoom.needRebuffer = True
                   self.curRoom.allDirty = True
                   self.drawing = False
                   if self.foregroundVisible == True:
                       self.foregroundVisible = False
                   else:
                       self.foregroundVisible = True
               elif newBrush == constants.nextMonster or newBrush == constants.prevMonster or newBrush == constants.nextAnimationSheet or newBrush == constants.prevAnimationSheet or newBrush == constants.nextSpriteSheet or newBrush == constants.prevSpriteSheet:
                   pass             
               else:
                   if self.brush == constants.buildWall:
                       self.drawing = False
                       pos = self.curRoom.getNearestVertex(mousepos, self.camera)
                       if pos != []:
                           self.wallPoints.append(pos)
                       
                       if len(self.wallPoints) == 2:
                           point1 = [self.wallPoints[0][0], self.wallPoints[0][1]]
                           point2 = [self.wallPoints[1][0], self.wallPoints[1][1]]
                           self.curRoom.uninitializedWallSegments.append([point1, point2])
                           self.wallPoints = []
                   elif self.brush in self.windowManager.monsterClassList:
                       pos = self.curRoom.getTileIndexByMouse(mousepos, self.camera)
                       if pos != []:
                           point = (pos[0] * constants.tileSize + 16, pos[1] * constants.tileSize + 16)
                           self.curRoom.uninitializedMonsters.append([self.brush, point])
                   elif self.brush == constants.playerPosition:
                       pos = self.curRoom.getTileIndexByMouse(mousepos, self.camera)
                       if pos != []:
                           point = (pos[0] * constants.tileSize, pos[1] * constants.tileSize)
                           self.curRoom.playerTestPosition = point
                   else:
                       pos = self.curRoom.getTileIndexByMouse(mousepos, self.camera)
                       if pos != [] and not self.brush == None: 
                           self.drawing = True
                       if isinstance(self.brush, AnimationSprite) and pos != []:
                           newAnimatedTile = AnimatedTile(copy.copy(self.brush), [pos[0]*constants.tileSize, pos[1]*constants.tileSize])
                           self.curRoom.addAnimatedTile(self.curLayer, newAnimatedTile)
                         
       if event.type == pygame.MOUSEBUTTONUP:
           if event.button == 1:
               self.drawing = False                    
       if event.type == pygame.KEYDOWN:
           print 'keydown'
           if event.key == pygame.K_q:
               print 'q'
               self.saveMap()

   def update(self, keys, mousePos, joystick, time):
       self.curRoom.update(time, keys, joystick)
       self.updateCamera( keys, mousePos, time)
       self.windowManager.updateFpsWindow(1/(time/1000.0))
       
       if self.drawing:
           pos = self.curRoom.getTileIndexByMouse(mousePos, self.camera)
           if pos != [] and not self.brush == None:
               if isinstance(self.brush, SheetSprite):
                   newTile = Tile(copy.copy(self.brush), [pos[0] * constants.tileSize, pos[1] * constants.tileSize])
                   self.curRoom.addTile(self.curLayer, newTile)
   
   def saveMap(self):
       fname = self.mapName
       saveFile = open('../data/default/maps/'+ fname + '.ttm', 'wb')
       print str(saveFile)
       saveMap = copy.copy(self.map)
       
       cPickle.dump(saveMap, saveFile)
       saveFile.close()
   
   def updateCamera(self, keys, mouse, time):
      x = 0;
      y = 0;
      if keys[pygame.K_a]:x+=1
      if keys[pygame.K_d]:x-=1
      if keys[pygame.K_w]:y+=1
      if keys[pygame.K_s]:y-=1
#      if mouse[0] <= 0:
#          x+=1
#      if mouse[0] >= constants.resolution[0] - 1:
#          x-=1
#      if mouse[1] <= 0:
#          y+=1
#      if mouse[1] >= constants.resolution[1] - 1:
#          y-=1
      
      self.camera = (self.camera[0] + x * constants.cameraSpeed[0] * time, self.camera[1] + y * constants.cameraSpeed[1] * time)