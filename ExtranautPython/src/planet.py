import constants
from room import *

class Planet():
    def __init__(self):
        self.rooms = []
        self.playerCheckPointRoom = [4, 2]
        self.playerMaxHp = 5
        self.playerArtifactsGathered = 0
        self.playerMaxJetpackFuel = 2000
        self.playerGunLevel = 1
        for i in range(0, constants.numRoomsX):
            self.rooms.append([])
            for j in range(0, constants.numRoomsY):
                self.rooms[i].append(Room((i,j)))
        self.playerStartingRoomPos = [0, 0]