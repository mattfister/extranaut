from roomData import *
import constants
import cPickle

class StateData():
    def __init__(self, planet):
        self.playerLoadRoom = planet.playerStartingRoomPos
        self.roomData = []
        for i in range(0, constants.numRoomsX):
            self.roomData.append([])
            for j in range(0, constants.numRoomsY):
                self.roomData.append(RoomData())
    
    def save(self, slotNum):
        fname = 'save.xns'
        saveFile = open('../saves/' + str(slotNum) + '/' + fname, 'wb')       
        cPickle.dump(self, saveFile)
        saveFile.close()
    
        