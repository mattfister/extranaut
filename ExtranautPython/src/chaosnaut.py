import cPickle
from planet import *
from room import *
import copy
from stateData import *
from chaosnautRoom import *
class Chaosnaut():
    def __init__(self, screen):
        self.screen = screen
       
        self.curRoom = ChaosnautRoom() 
        self.curRoom.startPhysicsSimulation()
        self.gameOver = False
        self.font = constants.defaultFont
        
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
                newPosition = (playerPosition[0], 16)
            elif offsetY < 0:
                newPosition = (playerPosition[0], (constants.roomSizeY - 1) * constants.tileSize + 16)
            print self.curRoomPos
            oldPlayer = copy.copy(self.curRoom.player)
            self.curRoom.stopPhysicsSimulation()
            self.curRoom = self.planet.rooms[self.curRoomPos[0]][self.curRoomPos[1]]
            self.curRoom.playerTestPosition = newPosition
            self.curRoom.startSimCopyPlayer(oldPlayer)
            self.curRoom.player.transitioning = True
            
    def testRoomTransition(self):
        pass
        
    def update(self, keys, mousePos, joystick, time):
        self.curRoom.update(time, keys, joystick)
        if self.curRoom.player.isDead():
            return self.handleDeadPlayer()
        else:
            self.testRoomTransition()
    
    def handleDeadPlayer(self):
        self.curRoom.stopPhysicsSimulation()
        return constants.chasonautGameOver
    
    def handleEvent(self, event, mousepos, keys):
        pass
    
    def draw(self, screen):
        self.curRoom.draw(screen, [0,0])
        if self.curRoom.player != None:
            self.curRoom.player.drawHpBar(screen)
            self.curRoom.player.drawFuelBar(screen)
        waveNumberText = 'Wave ' + str(self.curRoom.waveNumber)
        waveNumberRenderable = self.font.render(waveNumberText, 0, (255, 255, 255))
        screen.blit(waveNumberRenderable, (( self.curRoom.size[0] + 1, 1)))

        
        #self.curRoom.drawWalls(screen, self.camera)
        #self.windowManager.draw(screen, self.camera)