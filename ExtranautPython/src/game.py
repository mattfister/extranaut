import cPickle
from planet import *
from room import *
import copy
from stateData import *
from pauseMenu import *
import sys
import threading
import animationSprite

class SaveThread( threading.Thread ):
    def __init__(self, filename, planet, curRoomPos, curRoom):
        self.filename = filename
        self.planet = planet
        self.curRoomPos = curRoomPos
        self.curRoom = curRoom
        self.saving = False
        threading.Thread.__init__ ( self )
        
    def run(self):
        self.saving = True
        filePath = self.filename
        saveFile = open(filePath, 'rb')
        savePlanet = cPickle.load(saveFile)
        
    
        savePlanet.playerCheckPointRoom = copy.copy(self.curRoomPos)
        savePlanet.playerMaxHp = copy.copy(self.curRoom.player.maxHp)
        savePlanet.playerArtifactsGathered = copy.copy(self.curRoom.player.artifactsFound)
        savePlanet.playerMaxJetpackFuel = copy.copy(self.curRoom.player.maxJetPackFuel)
        savePlanet.playerGunLevel = copy.copy(self.curRoom.player.gunLevel)
        
        saveFile.close()
        
        saveFile = open(filePath, 'wb')
        
        for roomRow in savePlanet.rooms:
           for room in roomRow:
               room.prepForPickling()
               room.powerupTaken = self.planet.rooms[room.planetPos[0]][room.planetPos[1]].powerupTaken
        cPickle.dump(savePlanet, saveFile)           
        saveFile.close()
        self.saving = False    
     

class Game():
    def __init__(self, screen, saveGame, saveSlot):
        self.savingAnimation = AnimationSprite('savePoint', 1)
        self.animationFrameTimeout = 60
        self.animationFrame = 0
        
        self.screen = screen
        self.gameOver = False
        self.saveSlot = saveSlot
        self.saveGame = saveGame
        self.subMode = None
        self.saving = False
        self.saveThread = None
        
        fname = saveGame
        loadFile = open(saveGame, 'rb')
        self.planet = cPickle.load(loadFile)
        
        loadFile.close()
        
        
        self.stateData = None
        
        
        self.roomCursorX = 0
        self.roomCursorY = 0

        self.curRoomPos = copy.copy(self.planet.playerCheckPointRoom)
        self.curRoom = self.planet.rooms[self.curRoomPos[0]][self.curRoomPos[1]]
        self.curRoom.prepFromUnpickling()
        self.curRoom.startPhysicsSimulation()
        
        self.curRoom.player.maxHp = self.planet.playerMaxHp
        self.curRoom.player.curHp = self.curRoom.player.maxHp
        self.curRoom.player.artifactsFound = self.planet.playerArtifactsGathered 
        self.curRoom.player.maxJetPackFuel = self.planet.playerMaxJetpackFuel
        self.curRoom.player.gunLevel = self.planet.playerGunLevel
    
        
                
    def cacheRooms(self):
        pass
        #leftX = self.curRoomPos[0] - 3
        #if leftX < 0: 
        #    leftX = 0
            
        #rightX = self.curRoomPos[0] + 3
        #if rightX >= constants.numRoomsX:
        #    rightX = constants.numRoomsX - 1
        
        #topY = self.curRoomPos[1] - 3
        #if topY < 0:
        #    topY = 0
        
        #bottomY = self.curRoomPos[1] + 3
        #if bottomY >= constants.numRoomsY:
        #    bottomY = constants.numRoomsY - 1
        
        #for roomRow in self.planet.rooms[topY:bottomY]:
        #    for room in roomRow[leftX:rightX]:
        #        room.prepFromUnpickling()
        #        room.startPhysicsSimulation()
        #        room.stopPhysicsSimulation()
        
    def transitionRoom(self, offsetX, offsetY):
        if self.curRoom.player.transitioning == False:            
            self.curRoomPos[0] += offsetX
            self.curRoomPos[1] += offsetY
            if self.curRoomPos[0] < 0:
                self.curRoomPos[0] = 0
                return
            if self.curRoomPos[0] > constants.numRoomsX - 1:
                self.curRoomPos[0] = constants.numRoomsX - 1
                return
            if self.curRoomPos[1] < 0:
                self.curRoomPos[1] = 0
                return
            if self.curRoomPos[1] > constants.numRoomsY - 1:
                self.curRoomPos[1] = constants.numRoomsY - 1
                return
            
             
            playerPosition = self.curRoom.player.getScreenPosition((0,0))
            if offsetX > 0:
                newPosition = (16, playerPosition[1]+16)
            elif offsetX < 0:
                newPosition = ((constants.roomSizeX - 1) * constants.tileSize + 16, playerPosition[1]+16)
            elif offsetY > 0:
                newPosition = (playerPosition[0] + 16, 16)
            elif offsetY < 0:
                newPosition = (playerPosition[0] + 16, (constants.roomSizeY - 1) * constants.tileSize - 16)
            oldPlayer = copy.copy(self.curRoom.player)
            self.curRoom.stopPhysicsSimulation()
            self.curRoom.prepForPickling()
            
            self.curRoom = self.planet.rooms[self.curRoomPos[0]][self.curRoomPos[1]]
            self.curRoom.playerTransitionPosition = copy.copy(newPosition)

            self.curRoom.allDirty = True
            self.curRoom.prepFromUnpickling()
            
            self.curRoom.startSimCopyPlayer(oldPlayer)
            
            self.curRoom.player.transitioning = True
            
            
    def testRoomTransition(self):
        playerPosition = self.curRoom.player.getScreenPosition((0,0))
        if playerPosition[0] >= (constants.roomSizeX - 1) * constants.tileSize:
            self.transitionRoom(1, 0)
        elif playerPosition[0] <= 0:
            self.transitionRoom(-1, 0)
        elif playerPosition[1] >= (constants.roomSizeY - 1) * constants.tileSize - 10:
            self.transitionRoom(0, 1)
        elif playerPosition[1] - 10 <= 0:
            self.transitionRoom(0, -1)
        else:
            self.curRoom.player.transitioning = False
        
    def testWonGame(self):
        playerPosition = self.curRoom.player.getScreenPosition((0,0))
        if self.curRoomPos[1] == 9 and playerPosition[1] >= constants.roomSizeY  * constants.tileSize:
            return True
        else:
            return False
    
    def saveTheGame(self):
        self.planet.playerCheckPointRoom = copy.copy(self.curRoomPos)
        self.curRoom.player.curHp = copy.copy(self.curRoom.player.maxHp)
        if self.saveThread == None:
            self.saveThread = SaveThread(copy.copy(self.saveGame), copy.copy(self.planet), copy.copy(self.curRoomPos), copy.copy(self.curRoom))
            self.saveThread.start()
        #filePath = self.saveGame
        #saveFile = open(filePath, 'rb')
        #savePlanet = cPickle.load(saveFile)
        
        #self.planet.playerCheckPointRoom = copy.copy(self.curRoomPos)
        #savePlanet.playerCheckPointRoom = copy.copy(self.curRoomPos)
        #savePlanet.playerMaxHp = copy.copy(self.curRoom.player.maxHp)
        #self.curRoom.player.curHp = copy.copy(self.curRoom.player.maxHp)
        #savePlanet.playerArtifactsGathered = copy.copy(self.curRoom.player.artifactsFound)
        #savePlanet.playerMaxJetPackFuel = copy.copy(self.curRoom.player.maxJetPackFuel)
        #savePlanet.playerGunLevel = copy.copy(self.curRoom.player.gunLevel)
        
        #saveFile.close()
        
        #saveFile = open(filePath, 'wb')
        
        #for roomRow in savePlanet.rooms:
        #       for room in roomRow:
        #           room.prepForPickling()
        #           room.powerupTaken = self.planet.rooms[room.planetPos[0]][room.planetPos[1]].powerupTaken
        #cPickle.dump(savePlanet, saveFile)
               
        #saveFile.close()
        
        
    def update(self, keys, mousePos, joystick, time):
        if self.subMode == None:
            self.curRoom.update(time, keys, joystick)
            if self.curRoom.savePlanetNeeded == True:
                self.curRoom.savePlanetNeeded = False
                self.saveTheGame()
            if self.curRoom.player.isDead():
                self.handleDeadPlayer()
            else:
                if self.testWonGame() == True:
                    return constants.wonGameReturn
                self.testRoomTransition()
        else:
            self.subMode.update(keys, mousePos, joystick, time)
        self.animationFrameTimeout -= time
        if self.animationFrameTimeout <= 0:
            self.animationFrameTimeout = 60
            self.animationFrame += 1
            if self.animationFrame > 3:
                self.animationFrame = 0
                self.animationFrameTimeout = 60
        if self.saveThread != None and self.saveThread.isAlive() == False:
            self.saveThread = None
            
    def handleDeadPlayer(self):
        oldPlayer = copy.copy(self.curRoom.player)
        self.curRoom.stopPhysicsSimulation()
        self.curRoomPos = copy.copy(self.planet.playerCheckPointRoom)
        self.curRoom = self.planet.rooms[self.curRoomPos[0]][self.curRoomPos[1]]
        self.curRoom.prepFromUnpickling()
        self.curRoom.startSimCopyPlayer(oldPlayer)
        
        
    def handleEvent(self, event, mousepos, keys):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.subMode == None:
                self.subMode = PauseMenu(self.screen)
            else:
                self.subMode = None
        else:
            if self.subMode != None:
                eventReturn = self.subMode.handleEvent(event, mousepos, keys)
                if eventReturn == constants.quitToTitleReturn:
                    return constants.quitToTitleReturn
                if eventReturn == constants.quitToDesktopReturn:
                    sys.exit()
                if eventReturn == constants.resumeGame:
                    self.subMode = None 
    
    def draw(self, screen):
        if self.subMode == None:
            self.curRoom.draw(screen, [0,0])
            self.curRoom.player.drawHpBar(screen)
            self.curRoom.player.drawFuelBar(screen)
            #self.curRoom.drawWalls(screen, self.camera)
            #self.windowManager.draw(screen, self.camera)
        else:
            self.subMode.draw(screen)
        if self.saveThread != None and self.saveThread.saving == True:
            saveFrame = self.savingAnimation.getFrame(self.animationFrame)
            screen.blit(saveFrame, (0,0))