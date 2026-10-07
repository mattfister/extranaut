from sheetSprite import *
import pygame
import constants
import math
import pymunk
import copy
from tile import *
from animatedTile import *
from playerCharacter import *
from pymunkShims import *
from particleSystem import *
from sounds import *

class Room():
    def __init__(self, planetPos):
        self.planetPos = planetPos
        self.uninitializedWallSegments = []
        self.walls = []
        
        self.uninitializedMonsters = []
        self.monsters = []
        self.projectiles = []
        
        self.breakables = []
        self.backgroundTiles = []
        self.animatedBackgroundTiles = []
        self.midgroundTiles = []
        self.animatedMidgroundTiles = []
        self.foregroundTiles = []
        self.animatedForegroundTiles = []
        self.connectors = []
        
        self.dirtyPos = []
        
        self.allDirty = False
        
        size = (constants.tileSize * constants.roomSizeX, constants.tileSize * constants.roomSizeY)
        
        self.backgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        self.midgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        self.foregroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        
        self.border = pygame.Rect([0, 0, constants.tileSize * constants.roomSizeX, constants.tileSize * constants.roomSizeY])
        
        self.needRebuffer = False
        
        self.space = pymunk.Space()
        
        self.space.gravity = (0.0, constants.worldGrav)
    
        self.space.resize_static_hash()
        self.space.resize_active_hash()
        
        self.space.add_collision_handler(0, 0, None, None, collisionCallback, None)
        self.simulation = False
        
        self.playerTestPosition = None
        self.playerTransitionPosition = None
        
        self.player = None
        
        self.particleSystem = ParticleSystem()
        self.stateData = None
        
        self.music = None
        
        self.savePlanetNeeded = False
        
        self.powerupTaken = False
        
    def setStateData(self, state):
        self.stateData = state
        
    def initializeWalls(self):
        for uninitializedWallSegment in self.uninitializedWallSegments:
            wallBody = pymunk.Body(pymunk.inf, pymunk.inf)
            wallShape = pymunk.Segment(wallBody, copy.copy(uninitializedWallSegment[0]), copy.copy(uninitializedWallSegment[1]), .0)
            wallShape.friction = .5
            wallShape.collision_type = 0
            self.space.add_static(wallShape)
            self.walls.append(wallShape)
    
    def initializeMonsters(self):
        for [uninitializedMonsterConstructor, position] in self.uninitializedMonsters:
            newMonster = uninitializedMonsterConstructor(position)
            if self.powerupTaken and newMonster.isPowerup:
                continue
            else:
                self.monsters.append(newMonster)
        for monster in self.monsters:
            monster.initialize(self.space)
    
    def startPhysicsSimulation(self):
        if self.simulation == False:
            self.simulation = True
            self.initializeWalls()
            self.initializeMonsters()
            if self.playerTestPosition != None:
                self.player = PlayerCharacter(self.playerTestPosition)
                self.space.add(self.player.body, self.player.shape)
            if self.music != None:
                sounds.playMusic(self.music, 0.3)
                
    def startSimCopyPlayer(self, oldPlayer):
        if self.simulation == False:
            self.simulation = True
            self.initializeWalls()
            self.initializeMonsters()
            if self.playerTransitionPosition != None:
                self.player = PlayerCharacter(copy.copy(self.playerTransitionPosition))
                self.player.jetPackFuel = oldPlayer.jetPackFuel
                self.player.curHp = copy.copy(oldPlayer.curHp)
                self.player.maxHp = copy.copy(oldPlayer.maxHp)
                self.player.gunLevel = copy.copy(oldPlayer.gunLevel)
                self.player.maxJetPackFuel = copy.copy(oldPlayer.maxJetPackFuel)
                self.player.artifactsFound = copy.copy(oldPlayer.artifactsFound)
                self.player.body._set_velocity(oldPlayer.body._get_velocity())
                self.player.facingRight = copy.copy(oldPlayer.facingRight)
                self.space.add(self.player.body, self.player.shape)
                self.playerTransitionPosition = None
            elif self.playerTestPosition != None:
                self.player = PlayerCharacter(copy.copy(self.playerTestPosition))
                self.player.jetPackFuel = copy.copy(oldPlayer.jetPackFuel)
                self.player.curHp = copy.copy(oldPlayer.maxHp)
                self.player.maxHp = copy.copy(oldPlayer.maxHp)
                self.player.gunLevel = copy.copy(oldPlayer.gunLevel)
                self.player.maxJetPackFuel = copy.copy(oldPlayer.maxJetPackFuel)
                
                self.player.artifactsFound = copy.copy(oldPlayer.artifactsFound)
                self.player.body._set_velocity(oldPlayer.body._get_velocity())
                self.space.add(self.player.body, self.player.shape)
                self.player.facingRight = copy.copy(oldPlayer.facingRight)
            if self.music != None:
                sounds.playMusic(self.music, 0.1)
            print 'maxJetPackFuel = ' + str(self.player.maxJetPackFuel)
            print 'gunLevel = ' + str(self.player.gunLevel)
            print 'maxHp = ' + str(self.player.maxHp)
    def stopPhysicsSimulation(self): 
        if self.simulation == True:
            print 'stopping physics simulation'
            print 'player test position' + str(self.playerTestPosition)
            self.space = pymunk.Space()
            self.space.gravity = (0.0, constants.worldGrav)
            self.space.resize_static_hash()
            self.space.resize_active_hash()
            self.space.add_collision_handler(0, 0, None, None, collisionCallback, None)
            self.walls = []
            self.monsters = []
            self.projectiles = []
            self.simulation = False
            self.player = None
            self.particleSystem.clear()
            print 'stopping physics simulation'
            print 'player test position' + str(self.playerTestPosition)
            
    def bufferTiles(self):
        if self.allDirty:
            size = (constants.tileSize * constants.roomSizeX, constants.tileSize * constants.roomSizeY)
            self.backgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
            self.midgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
            self.foregroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
            for tile in self.backgroundTiles:
                tile.draw(self.backgroundImage, [0,0])
            for tile in self.midgroundTiles:
                tile.draw(self.midgroundImage, [0,0])
            for tile in self.foregroundTiles:
                tile.draw(self.foregroundImage, [0,0])
        else:
            for tile in self.backgroundTiles:
                for dirty in self.dirtyPos:
                    if self.allDirty or (dirty[0] == tile.pos[0] and dirty[1] == tile.pos[1]):
                        tile.draw(self.backgroundImage, [0,0])
            for tile in self.midgroundTiles:
                for dirty in self.dirtyPos:
                    if self.allDirty or (dirty[0] == tile.pos[0] and dirty[1] == tile.pos[1]):
                        tile.draw(self.midgroundImage, [0,0])
            for tile in self.foregroundTiles:
                for dirty in self.dirtyPos:
                    if self.allDirty or (dirty[0] == tile.pos[0] and dirty[1] == tile.pos[1]):
                        tile.draw(self.foregroundImage, [0,0])
        self.dirtyPos = []
        self.needRebuffer = False
        self.allDirty = False
        
    def draw(self, screen, camera, backgroundVisible = True, midgroundVisible = True, foregroundVisible = True):
        if self.needRebuffer:
            print 'buffering tiles'
            self.bufferTiles()
        
        if backgroundVisible:
            screen.blit(self.backgroundImage, camera)
        
            for tile in self.animatedBackgroundTiles:
                tile.draw(screen, camera)
        
        if midgroundVisible:
            screen.blit(self.midgroundImage, camera)
        
            for tile in self.animatedMidgroundTiles:
                tile.draw(screen, camera)
        
            self.drawMonsters(screen, camera)
        
        if foregroundVisible:
            screen.blit(self.foregroundImage, camera)
        
            for tile in self.animatedForegroundTiles:
                tile.draw(screen, camera)

        translatedBorder = pygame.Rect([self.border[0] + camera[0], self.border[1] + camera[1], self.border[2], self.border[3]])
        pygame.draw.rect(screen, (20, 20, 20), translatedBorder, 1)
    
    def drawMonsters(self, screen, camera):
        if self.simulation == True:
            for monster in self.monsters:
                monster.draw(screen, camera)
            for projectile in self.projectiles:
                projectile.draw(screen, camera)
            if self.player != None:
                self.player.draw(screen, camera)
            self.particleSystem.draw(screen, camera)
        else:
            for [monster, position] in self.uninitializedMonsters:
                tempMonster = monster(position)
                tempMonster.drawStatic(screen, [position[0] + camera[0], position[1] + camera[1]])
                tempMonster.shape.object = None #break the cycle!
    
    def drawWalls(self, screen, camera):
        if self.simulation == True:
            for wall in self.walls:
                body = wall.body

                pv1 = body.position + wall.a.rotated(body.angle)
                pv2 = body.position + wall.b.rotated(body.angle)
                p1 = pv1[0] + camera[0], pv1[1] + camera[1]
                p2 = pv2[0] + camera[0], pv2[1] + camera[1]
                
                pygame.draw.lines(screen, (0, 255, 0), False, [p1,p2])
        else:
            for segment in self.uninitializedWallSegments:
                p1 = segment[0][0] + camera[0], segment[0][1] + camera[1]
                p2 = segment[1][0] + camera[0], segment[1][1] + camera[1]
                pygame.draw.lines(screen, (0, 255, 0), False, [p1, p2])
            pass
         
    def update(self, time, keys, joystick):
        if time > 100:
            return
        for tile in self.animatedBackgroundTiles:
            tile.update(time)
        for tile in self.animatedMidgroundTiles:
            tile.update(time)
        for tile in self.animatedForegroundTiles:
            tile.update(time)
        
        if self.simulation:
            newParticles = []
            for projectile in self.projectiles:
                projectile.update(time)
            for monster in self.monsters:
                monster.update(time, self.player, self.monsters)
                if monster.savePlanetNeeded == True:
                    monster.savePlanetNeeded = False
                    self.savePlanetNeeded = True
                    if monster.isPowerup:
                        self.powerupTaken = True
                        
            self.particleSystem.update(time)
            fps = 1/(time/1000.0)
            iterations = 25
            dt = 1.0/float(fps)/float(iterations)
            for x in range(iterations): # 10 iterations to get a more stable simulation
                self.space.step(dt)
            if self.player != None:
                self.player.update(time, keys, joystick)
            for monster in self.monsters:
                for proj in monster.projectilesToFire:
                    self.projectiles.append(proj)
                    proj.initialize(self.space)
                monster.projectilesToFire = []
                
                for part in monster.particlesToEmit:
                    newParticles.append(part)
                monster.particlesToEmit = []
            
            for proj in self.projectiles:
                for part in proj.particlesToEmit:
                    newParticles.append(part)
                proj.particlesToEmit = []
                
            for proj in self.player.projectilesToFire:
                proj.initialize(self.space)
                self.projectiles.append(proj)
            self.player.projectilesToFire = []
            
            for part in self.player.particlesToEmit:
                newParticles.append(part)
            self.player.particlesToEmit = []
            
            for particle in newParticles:
                self.particleSystem.addParticle(particle)
            
            self.cleanupFromUpdate()
            
            
    def cleanupFromUpdate(self):
        newProjectiles = []
        deadPhysicsStuff = []
        for projectile in self.projectiles:
            if projectile.isDead() == False:
                newProjectiles.append(projectile)
            else:
                self.space.remove(projectile.shape)
                self.space.remove(projectile.body)
        
        self.projectiles = newProjectiles
        
        newMonsters = []
        for monster in self.monsters:
            if monster.isDead() == False:
                newMonsters.append(monster)
            else:
                if monster.savePlanetNeeded == True:
                    monster.savePlanetNeeded = False
                    self.savePlanetNeeded = True
                    if monster.isPowerup:
                        self.powerupTaken = True
                monster.addDeathParticles()
                for particle in monster.particlesToEmit:
                    self.particleSystem.addParticle(particle)
                self.space.remove(monster.shape)
                self.space.remove(monster.body)
                
        self.monsters = newMonsters
        
        self.space.remove(deadPhysicsStuff)
        
        
    def addTile(self, layer, newTile):
        tilesToKeep = []
        tileLayer = None
        if layer == 'midground':
            tileLayer = self.midgroundTiles
        elif layer == 'background':
            tileLayer = self.backgroundTiles
        elif layer == 'foreground':
            tileLayer = self.foregroundTiles
            
        for tile in tileLayer:
            if tile.pos[0] != newTile.pos[0] or tile.pos[1] != newTile.pos[1]:
                tilesToKeep.append(tile)
        if layer == 'midground':
            self.midgroundTiles = tilesToKeep
            self.midgroundTiles.append(newTile)
        if layer == 'background':
            self.backgroundTiles = tilesToKeep
            self.backgroundTiles.append(newTile)
        if layer == 'foreground':
            self.foregroundTiles = tilesToKeep
            self.foregroundTiles.append(newTile)
        
        self.dirtyPos.append(newTile.pos)
        
        self.needRebuffer = True
    
    def addAnimatedTile(self, layer, newAnimatedTile):
        tileLayer = None
        if layer == 'midground':
            self.animatedMidgroundTiles.append(newAnimatedTile)
        elif layer == 'background':
            self.animatedBackgroundTiles.append(newAnimatedTile)
        elif layer == 'foreground':
            self.animatedForegroundTiles.append(newAnimatedTile)
        for tile in self.animatedMidgroundTiles:
            tile.frameNum = 0
            tile.timeOut = constants.animationFrameTimeOut
        for tile in self.animatedBackgroundTiles:
            tile.frameNum = 0
            tile.timeOut = constants.animationFrameTimeOut
        for tile in self.animatedForegroundTiles:
            tile.frameNum = 0
            tile.timeOut = constants.animationFrameTimeOut
            
    def getTileIndexByMouse(self, mousePos, cameraPos):  
        if mousePos[0] < cameraPos[0] or mousePos[0] > constants.roomSizeX * constants.tileSize + cameraPos[0]:
            return []
        if mousePos[1] < cameraPos[1] or mousePos[1] > constants.roomSizeY * constants.tileSize + cameraPos[1]:
            return []
        return [int(math.fabs(math.floor((cameraPos[0] - mousePos[0])/constants.tileSize)))-1, int(math.fabs(math.floor((cameraPos[1] - mousePos[1])/constants.tileSize)))-1]
    
    def getNearestVertex(self, mousePos, cameraPos):
        pos = [0,0]
        pos[0] = mousePos[0] - cameraPos[0] 
        pos[1] = mousePos[1] - cameraPos[1]
        if mousePos[0] < cameraPos[0] or mousePos[0] > constants.roomSizeX * constants.tileSize + cameraPos[0]:
            return []
        if mousePos[1] < cameraPos[1] or mousePos[1] > constants.roomSizeY * constants.tileSize + cameraPos[1]:
            return []
        return [round(float(pos[0])/float(constants.tileSize))* constants.tileSize, round(float(pos[1])/float(constants.tileSize))* constants.tileSize]
    
    def prepForPickling(self):
        self.needRebuffer = True
        self.backgroundImage = None
        self.midgroundImage = None
        self.foregroundImage = None
        self.space = None
        
    def prepFromUnpickling(self):
        size = (constants.tileSize * constants.roomSizeX, constants.tileSize * constants.roomSizeY)
        self.backgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        self.midgroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        self.foregroundImage = pygame.Surface((size), pygame.SRCALPHA, 32);
        self.allDirty = True
        self.bufferTiles()
        self.space = pymunk.Space()
        self.space.gravity = (0.0, constants.worldGrav)
        self.space.resize_static_hash()
        self.space.resize_active_hash()
        self.space.add_collision_handler(0, 0, None, None, collisionCallback, None)

    def popAnimation(self, layer):
        if layer == 'midground':
            if len(self.animatedMidgroundTiles) > 0:
                self.animatedMidgroundTiles.pop()
        elif layer == 'background':
            if len(self.animatedBackgroundTiles) > 0:
                self.animatedBackgroundTiles.pop()
        elif layer == 'foreground':
            if len(self.animatedForegroundTiles) > 0:
                self.animatedForegroundTiles.pop()
    
    def popWall(self):
        if len(self.uninitializedWallSegments) > 0:
            self.uninitializedWallSegments.pop()
    
    def popMonster(self):
        if len(self.uninitializedMonsters) > 0:
            self.uninitializedMonsters.pop()