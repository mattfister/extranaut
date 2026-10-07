import pymunk
import pygame
import copy
import spriteSheetManager
from animationSprite import *
from sheetSprite import *
import math
import random
from pymunkShims import *
from projectile import *
import sounds

class Monster():
    def __init__(self, uninitializedBody, uninitializedShape):
        self.body = uninitializedBody
        self.shape = uninitializedShape
        self.projectilesToFire = []
        self.damagePlayerOnTouch = False
        self.damagedByProjectiles = True
        self.maxHp = 1
        self.curHp = self.maxHp
        self.particlesToEmit = []
        self.hitTimeout = 100
        self.angry = False
        self.deathSound = None
        self.hitSound = 'hit'
        self.savePlanetNeeded = False
        self.isPowerup = False
        
    def draw(self, screen, camera):
        pass
    
    def initialize(self, space):
        space.add(self.body, self.shape)
    
    def uninitialize(self):
        self.body = None
        self.shape = None
    
    def drawStatic(self, screen, pos):
        pass

    def isDead(self):
        return self.curHp <= 0
    
    def hit(self):
        self.curHp = self.curHp - 1
        if self.curHp <= 0:
            if self.deathSound != None:
                sounds.playEffect(self.deathSound)
        else:
            sounds.playEffect(self.hitSound)
            
    def update(self, time, player, monsters):
        self.hitTimeout -= time
    
    def addDeathParticles(self):
        pass
    
    def handleCollision(self, selfShape, collisionShape, consacts):
        if isinstance(collisionShape, ObjectCircle):
            if isinstance(collisionShape.object, Projectile):
               if self.damagedByProjectiles and collisionShape.object.damageMonsters:
                   if self.hitTimeout <= 0:
                       self.hit()
                       self.hitTimeout = 100
        
class BallMonster(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('ballMonster', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = False
        self.deathSound = 'deadAlien'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 3000)
            self.body.apply_impulse((random.choice([-5000, 0, 5000]),random.choice([-5000, 0, 5000])), (0,0))
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class JumpBot(Monster):
    def __init__(self, position):
        mass = 20
        radius = 16
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        self.maxHp = 3
        self.curHp = 3
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('bots2', 0)
        self.jumpTimerTimeout = 500 
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = 1000
        self.damagePlayerOnTouch = True
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
    
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        if self.jumpTimerTimeout > 0:
            image = self.animatedSprite.getFrame(1)
        else:
            image = self.animatedSprite.getFrame(0)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        playerPos = player.getScreenPosition((0,0))
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        
        self.jumpTimerTimeout -= time

        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer = 1000
            playerNearby = abs(myPos[0] - playerPos[0]) < 150 and abs(myPos[1] - playerPos[1]) < 150
            if playerNearby:
                right = playerPos[0] > myPos[0]
                if right:
                    self.body.apply_impulse((5000, -8000), (0,0))
                else:
                    self.body.apply_impulse((-5000, -8000), (0,0))
            else:
                self.body.apply_impulse((0,-8000), (0,0))
            self.jumpTimerTimeout = 500
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class Beast(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        self.facing = random.choice(['left', 'right'])
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 5
        self.curHp = 5
        if self.facing == 'left':
            self.body._set_velocity((-200, self.body._get_velocity()[1]))
        else:
            self.body._set_velocity((200, self.body._get_velocity()[1]))
        self.animatedSpriteLeft = AnimationSprite('beast', 0)
        self.animatedSpriteRight = AnimationSprite('beast', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        self.switchDirectionTimer = random.randint(2000, 10000)
        self.justSwitchedTimer = 1000
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        if self.facing == 'left':
            image = self.animatedSpriteLeft.getSizedFrame(64, self.animationFrame)
        else:
            image = self.animatedSpriteRight.getSizedFrame(64, self.animationFrame)
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        self.justSwitchedTimer -= time
        switch = False
        if abs(self.body._get_velocity()[0]) < 50 and self.justSwitchedTimer <= 0:
            self.animationFrame = 0
            self.animationTimer = constants.animationFrameTimeOut
            if self.facing == 'left':
                self.facing = 'right'
            elif self.facing == 'right':
                self.facing = 'left'
            
            self.justSwitchedTimer = 1000
        if self.facing == 'left':
            self.body._set_velocity((-200, self.body._get_velocity()[1]))
        else:
            self.body._set_velocity((200, self.body._get_velocity()[1]))
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 2:
                self.animationFrame = 0
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSpriteRight.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])


class OrbBoss(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 20
        self.curHp = 20
        self.animationSprite1 = AnimationSprite('orbBoss', 0)
        self.animationSprite2 = AnimationSprite('orbBoss', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 1)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        self.switchDirectionTimer = random.randint(2000, 10000)
        self.mode = random.choice(['Chasing', 'Flying'])
        self.modeTimer = random.randint(5000, 10000)
        self.shootTimer = 1000
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 100
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
                
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        if self.mode == 'Chasing':
            image = self.animationSprite1.getSizedFrame(64, self.animationFrame)
        else:
            image = self.animationSprite2.getSizedFrame(64, self.animationFrame)
            
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])

    def update(self, time, player, monsters):
        playerPos = player.getScreenPosition((0,0))
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        self.modeTimer -= time
        if self.modeTimer <= 0:
            if self.mode == 'Chasing':
                self.mode = 'Flying'
            elif self.mode == 'Flying':
                self.mode = 'Chasing'
            self.modeTimer = random.randint(5000, 10000)
        
        if self.mode == 'Flying':
            self.forceTimer -= time
            if self.forceTimer < 0:
                self.forceTimer = random.randint(0, 100)
                self.body.apply_impulse((random.choice([-1000, 0, 1000]),-15000), (0,0))
            self.shootTimer -= time
            if self.shootTimer <= 0:
                self.shootTimer = 1000
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] - constants.tileSize), [random.randint(-10000, 10000), random.randint(-15000, -10000)]))
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] - constants.tileSize), [random.randint(-10000, 10000), random.randint(-15000, -10000)]))
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] - constants.tileSize), [random.randint(-10000, 10000), random.randint(-15000, -10000)]))

        
        if self.mode == 'Chasing':
            right = playerPos[0] > myPos[0]
            down = playerPos[1] > myPos[1]
            self.forceTimer -= time
            if self.forceTimer < 0:
                self.forceTimer = 60
                if right:
                    self.body.apply_impulse((5000, 0), (0,0))
                else:
                    self.body.apply_impulse((-5000, 0), (0,0))
        
                if not down:
                    self.body.apply_impulse((0, -15000), (0,0))
                else:
                    self.body.apply_impulse((0, 5000), (0,0))

        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame > 1:
                self.animationFrame = 0
        
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animationSprite1.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class FallenExtranaut(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 20
        self.curHp = 20
        self.animationSprite1 = AnimationSprite('fallenExtranaut', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 1)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        self.switchDirectionTimer = random.randint(2000, 10000)
        self.mode = random.choice(['Chasing', 'Flying'])
        self.modeTimer = random.randint(5000, 10000)
        self.shootTimer = 1000
        self.deathSound = 'explode'
        self.fireTimeout = 2000
        
    def addDeathParticles(self):
        numToEmit = 100
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
                
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        
        image = self.animationSprite1.getSizedFrame(64, self.animationFrame)
            
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])

    def update(self, time, player, monsters):
        playerPos = player.getScreenPosition((0,0))
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        self.modeTimer -= time
        if self.modeTimer <= 0:
            if self.mode == 'Chasing':
                self.mode = 'Flying'
            elif self.mode == 'Flying':
                self.mode = 'Chasing'
            self.modeTimer = random.randint(5000, 10000)
        
        if self.mode == 'Flying':
            self.forceTimer -= time
            if self.forceTimer < 0:
                self.forceTimer = random.randint(0, 100)
                self.body.apply_impulse((random.choice([-1000, 0, 1000]),-15000), (0,0))
            self.shootTimer -= time
            if self.shootTimer <= 0:
                self.shootTimer = 1000
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] + 30), [random.randint(-10000, 10000), 0 ]))
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] + 30), [random.randint(-10000, 10000), 0 ]))
                self.projectilesToFire.append(EnergyGrenade((myPos[0] + 32, myPos[1] + 30), [random.randint(-10000, 10000), 0 ]))

        
        if self.mode == 'Chasing':
            right = playerPos[0] > myPos[0]
            down = playerPos[1] > myPos[1]
            self.forceTimer -= time
            if self.forceTimer < 0:
                self.forceTimer = 60
                if right:
                    self.body.apply_impulse((5000, 0), (0,0))
                else:
                    self.body.apply_impulse((-5000, 0), (0,0))
        
                if not down:
                    self.body.apply_impulse((0, -15000), (0,0))
                else:
                    self.body.apply_impulse((0, 5000), (0,0))
            self.fireTimeout -= time
            if self.fireTimeout <= 0:
                playerPos = player.getScreenPosition((0,0))
                v = self.body.position
                rot = self.body.rotation_vector
                myPos = int(v[0]), int(v[1])
                toPlayer = [playerPos[0] - myPos[0], playerPos[1] - myPos[1]]
                absToPlayer = math.sqrt(toPlayer[0] * toPlayer[0] + toPlayer[1] * toPlayer[1])
                toPlayer = [toPlayer[0]/absToPlayer * 7000, toPlayer[1]/absToPlayer * 7000]
                self.fireTimeout = 2000
                r = self.shape.radius
                v = self.body.position
                rot = self.body.rotation_vector
                position = int(v[0]), int(v[1])
                if toPlayer[0] > 0:
                    xOffset = 36
                else:
                    xOffset = -36
                if toPlayer[1] > 0:
                    yOffset = 36
                else:
                    yOffset = -36
                self.projectilesToFire.append(EnemyEnergyBall((position[0] + xOffset, position[1] + yOffset), (toPlayer[0], toPlayer[1])))
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame > 3:
                self.animationFrame = 0
        
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animationSprite1.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class OctoBoss(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        uninitializedBody.apply_force((0, -constants.worldGrav * mass))
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 20
        self.curHp = 20
        
        self.animationSprite1 = AnimationSprite('octoBoss', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 1)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        
        self.modeTimer = random.randint(5000, 10000)
        self.shootTimer = 1000
        self.impulseTimer = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.grenadeTimer = 5000
        self.deathSound = 'explode'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animationSprite1.getSizedFrame(64, 0)
        
            
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        self.forceTimer = random.randint(0, 100)
    
    def addDeathParticles(self):
        numToEmit = 100
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))    
    
    def update(self, time, player, monsters):
        playerPos = player.getScreenPosition((0,0))
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        
        self.shootTimer -= time
        if self.shootTimer <= 0:
            self.shootTimer = 1000
    
            playerPos = player.getScreenPosition((0,0))
            v = self.body.position
            rot = self.body.rotation_vector
            myPos = int(v[0]), int(v[1])
            toPlayer = [playerPos[0] - myPos[0], playerPos[1] - myPos[1]]
            absToPlayer = math.sqrt(toPlayer[0] * toPlayer[0] + toPlayer[1] * toPlayer[1])
            toPlayer = [toPlayer[0]/absToPlayer * 7000, toPlayer[1]/absToPlayer * 7000]
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            if toPlayer[0] > 0:
                xOffset = 34
            else:
                xOffset = -34
            if toPlayer[1] > 0:
                yOffset = 34
            else:
                yOffset = -34
            
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + xOffset, position[1] + yOffset), (toPlayer[0], toPlayer[1])))
        
        self.grenadeTimer -= time
        if self.grenadeTimer <= 0:
            self.grenadeTimer = 5000
            self.projectilesToFire.append(EnergyGrenade((myPos[0], myPos[1] + 48), [random.randint(-10000, 10000), 0]))
            self.projectilesToFire.append(EnergyGrenade((myPos[0], myPos[1] + 48), [random.randint(-10000, 10000), 0]))
            self.projectilesToFire.append(EnergyGrenade((myPos[0], myPos[1] + 48), [random.randint(-10000, 10000), 0]))
        
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.particlesToEmit.append(FlyBotParticle([random.randint(myPos[0] + 8, myPos[0] + 20), myPos[1] + 48]))    
            self.jetPackParticleToAddTimeOut = 30
                
        self.impulseTimer -= time
        if self.impulseTimer <= 0:
            hpLost = self.maxHp - self.curHp
            hpImpulse = 2000 * hpLost
            self.body.apply_impulse((random.choice([30000 + hpImpulse, -30000 - hpImpulse]), random.choice([1000 + hpImpulse, -1000 - hpImpulse])))
            self.impulseTimer = 2000
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame > 1:
                self.animationFrame = 0
        
    
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animationSprite1.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])


class HeadBoss(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 15
        self.curHp = 15
        
        self.animationSprite1 = AnimationSprite('snakeHeadBoss', 0)
        self.animationSprite2 = AnimationSprite('snakeHeadBoss', 1)
        
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.shieldTimer = 0
        self.damagePlayerOnTouch = True
        
        self.modeTimer = random.randint(5000, 10000)
        self.shootTimer = 1000
        self.impulseTimer = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.grenadeTimer = 5000
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 200
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
                
    def draw(self, screen, camera):
        
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        if self.shieldTimer > 0:
            image = self.animationSprite2.getSizedFrame(64, self.animationFrame)
        else:
            image = self.animationSprite1.getSizedFrame(64, self.animationFrame)
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters): 
        playerPos = player.getScreenPosition((0,0))
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        
        self.shootTimer -= time
        if self.shootTimer <= 0:
            self.shootTimer =  1000 -  (self.maxHp - self.curHp) * 50
    
            playerPos = player.getScreenPosition((0,0))
            v = self.body.position
            rot = self.body.rotation_vector
            myPos = int(v[0]), int(v[1])
            toPlayer = [playerPos[0] - myPos[0] + 32, playerPos[1] - myPos[1] + 32]
            absToPlayer = math.sqrt(toPlayer[0] * toPlayer[0] + toPlayer[1] * toPlayer[1])
            toPlayer = [toPlayer[0]/absToPlayer * 7000, toPlayer[1]/absToPlayer * 7000]
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            if toPlayer[0] > 0:
                xOffset = 34
            else:
                xOffset = -50
            yOffset = -16
            
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + xOffset, position[1] + yOffset), (toPlayer[0], toPlayer[1])))
        
        self.animationFrame = 0
        if playerPos[1] - myPos[1] < -500:
            self.animationFrame = 2
        elif playerPos[1] - myPos[1] < -100:
            self.animationFrame = 1
        
        self.shieldTimer -= time
                        
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animationSprite1.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

    def hit(self):
        if self.shieldTimer <= 0:
            self.curHp = self.curHp - 1
            if self.curHp <= 0:
                if self.deathSound != None:
                    sounds.playEffect(self.deathSound)
            else:
                sounds.playEffect(self.hitSound)
                
            self.shieldTimer = 2000
        
class SpikyHeadMonster(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('snakeHeadBoss', 4)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.forceTimer = 1000
        self.damagePlayerOnTouch = True
        self.deathSound = 'explode'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        if len(monsters) == 3:
            self.curHp = 0
        self.animationTimer -= time
        
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  1000
            self.body.apply_impulse((random.choice([-5000, 0, 5000]),random.choice([-5000, 0, 5000])), (0,0))
        
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

    def hit(self):
        pass

class HandBot(Monster):
    def __init__(self, position):
        radius = 32
        mass = 200
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 5
        self.curHp = 5
        self.animatedSprite = AnimationSprite('bigBots1', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 1)
        self.damagePlayerOnTouch = True
        self.justSwitchedTimer = 1000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getSizedFrame(64, self.animationFrame)
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
    
    def update(self, time, player, monsters):
        playerPos = player.getScreenPosition((0,0))
        self.justSwitchedTimer -= time
        v = self.body.position
        rot = self.body.rotation_vector
        myPos = int(v[0]), int(v[1])
        if abs(myPos[0] - playerPos[0]) < 100 and playerPos[1] < myPos[1]:
            self.body.apply_impulse((0, -5000))
            self.jetPackParticleToAddTimeOut -= time
            if self.jetPackParticleToAddTimeOut < 0:
                self.particlesToEmit.append(FlyBotParticle([random.randint(myPos[0] + 8, myPos[0] + 20), myPos[1] + 48]))
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame +=1 
            if self.animationFrame > 1:
                self.animationFrame = 0
                
        Monster.update(self, time, player, monsters)
        
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class ArtifactDoor(Monster):
    def __init__(self, position):
        radius = 32
        mass = 20000
        
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 100
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('artifactDoor', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.damagePlayerOnTouch = False
        self.dead = False
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getSizedFrame(64, self.animationFrame)

        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        if player.artifactsFound >= 4:
            self.dead = True
        else:
            self.dead = False
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 2:
                self.animationFrame = 0
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

    def hit(self):
        pass

    def isDead(self):
        return self.dead

class MonsterDoor(Monster):
    def __init__(self, position):
        radius = 32
        mass = 20000
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 100
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('artifactDoor', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.damagePlayerOnTouch = False
        self.dead = False
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getSizedFrame(64, self.animationFrame)

        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        if len(monsters) == 1:
            self.dead = True
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 2:
                self.animationFrame = 0
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

    def hit(self):
        pass

    def isDead(self):
        return self.dead

class MonsterDoor2(Monster):
    def __init__(self, position):
        radius = 32
        mass = 20000
        
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 100
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('artifactDoor', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.damagePlayerOnTouch = False
        self.dead = False
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getSizedFrame(64, self.animationFrame)

        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        if len(monsters) == 2:
            self.dead = True
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 2:
                self.animationFrame = 0
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getSizedFrame(64, 0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

    def hit(self):
        pass

    def isDead(self):
        return self.dead

class Flyer(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 2 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        
        self.animatedSprite = AnimationSprite('ballMonster', 3)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        self.deathSound = 'deadAlien'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 3000)
            self.body.apply_impulse((random.choice([-5000, 0, 5000]),random.randint(5000, 10000)), (0,0))
        
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class FlyBot(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 1.1 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 3
        self.curHp = 3 
        self.animatedSprite = AnimationSprite('bots', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 100)
        self.damagePlayerOnTouch = True
        self.fireTimeout = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
            
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 100)
            self.body.apply_impulse((random.choice([-1000, 0, 1000]),random.randint(-1000, 1000)), (0,0))
        self.fireTimeout -= time
        if self.fireTimeout < 0:
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + 32, position[1]), (7000, 7000)))
            self.projectilesToFire.append(EnemyEnergyBall((position[0] - 32, position[1]), (-7000, 7000)))
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.jetPackParticleToAddTimeOut = 30
            numToEmit = random.randint(1, 5)
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            for i in range(numToEmit):
                self.particlesToEmit.append(FlyBotParticle([random.choice([position[0] + 12, position[0] + 20]), position[1] + 30]))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class AimerTurret(Monster):
    def __init__(self, position):
        radius = 16
        mass = 1000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        uninitializedBody.apply_force((0, -constants.worldGrav * mass))
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 1
        self.curHp = 1
        self.animatedSprite = AnimationSprite('bots2', 2)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = 0
        self.damagePlayerOnTouch = True
        self.fireTimeout = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
         
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 2:
                self.animationFrame = 0
        self.fireTimeout -= time
        if self.fireTimeout < 0:
            playerPos = player.getScreenPosition((0,0))
            v = self.body.position
            rot = self.body.rotation_vector
            myPos = int(v[0]), int(v[1])
            toPlayer = [playerPos[0] - myPos[0], playerPos[1] - myPos[1]]
            absToPlayer = math.sqrt(toPlayer[0] * toPlayer[0] + toPlayer[1] * toPlayer[1])
            toPlayer = [toPlayer[0]/absToPlayer * 7000, toPlayer[1]/absToPlayer * 7000]
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            if toPlayer[0] > 0:
                xOffset = 36
            else:
                xOffset = -8
            if toPlayer[1] > 0:
                yOffset = 36
            else:
                yOffset = -8
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + xOffset, position[1] + yOffset), (toPlayer[0], toPlayer[1])))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class ChaosBot(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 1 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 1
        self.curHp = 1 
        self.animatedSprite = AnimationSprite('bots', 1)
        self.angryAnimatedSprite = AnimationSprite('bots', 2)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 100)
        self.damagePlayerOnTouch = True
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        if not self.angry:
            image = self.animatedSprite.getFrame(self.animationFrame)
        else:
            image = self.angryAnimatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
        
    def update(self, time, player, monsters):
        if self.angry == False:
            self.body._set_velocity((-100, self.body._get_velocity()[1]))
        else:
            self.body._set_velocity((-300, self.body._get_velocity()[1]))
            
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(500, 1000)
            if not self.angry:
                self.body.apply_impulse((0,random.randint(-3000, 3000)), (0,0))
            else:
                self.body.apply_impulse((1000, random.randint(-3000, 3000)), (0,0))
                
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.jetPackParticleToAddTimeOut = 30
            numToEmit = random.randint(1, 5)
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            for i in range(numToEmit):
                self.particlesToEmit.append(FlyBotParticle([random.choice([position[0] + 12, position[0] + 20]), position[1] + 30]))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class HoverBlock(Monster):
    def __init__(self, position):
        radius = 16
        mass = 4000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 20
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.initialPosition = position
        self.maxHp = 1
        self.curHp = 1 
        self.sprite = SheetSprite('chaosBlocks', [32, 128, 32, 32])
        self.damagePlayerOnTouch = False
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        
        image = self.sprite.getImage()
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        Monster.update(self, time, player, monsters)
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        dirToInitialX = self.initialPosition[0] - p[0]
        dirToInitialY = self.initialPosition[1] - p[1]
        self.body.apply_impulse((2 * dirToInitialX,2 * dirToInitialY), (0,0))
        
        
    def drawStatic(self, screen, pos):
        image = self.sprite.getImage()
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
class DefenseTurretVertical(Monster):
    def __init__(self, position):
        radius = 16
        mass = 5
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.body.apply_force((0, -constants.worldGrav))
        self.animatedSprite = AnimationSprite('turret', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.fireTimer = random.randint(0, 3000)
        self.damagePlayerOnTouch = False
        self.deathSound = 'explode'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.fireTimer -= time
        if self.fireTimer < 0:
            self.fireTimer =  3000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            p = int(v[0]), int(v[1])
            self.projectilesToFire.append(EnergyGrenade((p[0] + 8, p[1] - constants.tileSize), [random.randint(-10000, 10000), random.randint(-15000, -10000)]))
        
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class SavePoint(Monster):
    def __init__(self, position):
        radius = 16
        mass = 40000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 40000
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('savePoint', 0)
        self.animatedSpriteActivated = AnimationSprite('savePoint', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = False
        
        
    def draw(self, screen, camera):
        v = self.body.position
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer <= 0:
            self.animationFrame += 1
            self.animationTimer = constants.animationFrameTimeOut
        if self.animationFrame >= 4:
            self.animationFrame = 0
                    
        Monster.update(self, time, player, monsters)
        self.body._set_velocity((0,0))
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
    def hit(self):
        if self.animatedSprite != self.animatedSpriteActivated:
            self.animatedSprite = self.animatedSpriteActivated
            self.savePlanetNeeded = True

class HpPowerup(Monster):
    def __init__(self, position):
        radius = 16
        mass = 40000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 40000
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('collectibles', 2)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.damagePlayerOnTouch = False
        self.isPowerup = True
        self.powerupApplied = False
        self.maxHp = 1
        self.curHp = 1
        
    def draw(self, screen, camera):
        v = self.body.position
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer <= 0:
            self.animationFrame += 1
            self.animationTimer = constants.animationFrameTimeOut
        if self.animationFrame >= 4:
            self.animationFrame = 0
                    
        Monster.update(self, time, player, monsters)
        self.body._set_velocity((0,0))
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
    def hit(self):
        pass

    def applyPowerup(self, player):
        if not self.powerupApplied:
            sounds.playEffect('armorUpgrade')
            player.maxHp += 1
            player.curHp = player.maxHp
            self.powerupApplied = True
            self.curHp = 0
            self.savePlanetNeeded = True

class FuelPowerup(Monster):
    def __init__(self, position):
        radius = 16
        mass = 40000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 40000
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('collectibles', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.damagePlayerOnTouch = False
        self.isPowerup = True
        self.powerupApplied = False
        self.maxHp = 1
        self.curHp = 1
        
    def draw(self, screen, camera):
        v = self.body.position
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer <= 0:
            self.animationFrame += 1
            self.animationTimer = constants.animationFrameTimeOut
        if self.animationFrame >= 4:
            self.animationFrame = 0
                    
        Monster.update(self, time, player, monsters)
        self.body._set_velocity((0,0))
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
    def hit(self):
        pass

    def applyPowerup(self, player):
        if not self.powerupApplied:
            sounds.playEffect('jetpackUpgrade')
            player.maxJetPackFuel += 500
            self.powerupApplied = True
            self.curHp = 0
            self.savePlanetNeeded = True

class GunPowerup(Monster):
    def __init__(self, position):
        radius = 16
        mass = 40000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 40000
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('collectibles', 3)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.damagePlayerOnTouch = False
        self.isPowerup = True
        self.powerupApplied = False
        self.maxHp = 1
        self.curHp = 1
        
    def draw(self, screen, camera):
        v = self.body.position
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer <= 0:
            self.animationFrame += 1
            self.animationTimer = constants.animationFrameTimeOut
        if self.animationFrame >= 4:
            self.animationFrame = 0
                    
        Monster.update(self, time, player, monsters)
        self.body._set_velocity((0,0))
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
    def hit(self):
        pass

    def applyPowerup(self, player):
        if not self.powerupApplied:
            sounds.playEffect('gunUpgrade')
            player.gunLevel += 1
            self.powerupApplied = True
            self.curHp = 0
            self.savePlanetNeeded = True

class AlienArtifact(Monster):
    def __init__(self, position):
        radius = 16
        mass = 40000
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = 40000
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('collectibles', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.damagePlayerOnTouch = False
        self.isPowerup = True
        self.powerupApplied = False
        self.maxHp = 1
        self.curHp = 1
        
    def draw(self, screen, camera):
        v = self.body.position
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer <= 0:
            self.animationFrame += 1
            self.animationTimer = constants.animationFrameTimeOut
        if self.animationFrame >= 4:
            self.animationFrame = 0
                    
        Monster.update(self, time, player, monsters)
        self.body._set_velocity((0,0))
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
    
    def hit(self):
        pass

    def applyPowerup(self, player):
        if not self.powerupApplied:
            sounds.playEffect('alienArtifactAcquired')
            player.artifactsFound += 1
            self.powerupApplied = True
            self.curHp = 0
            self.savePlanetNeeded = True

class SpikyBallMonster(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('ballMonster', 2)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 5000)
        self.damagePlayerOnTouch = True
        self.deathSound = 'deadAlien'
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
        
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 3000)
            self.body.apply_impulse((random.choice([-5000, 0, 5000]),random.choice([-5000, 0, 5000])), (0,0))
        
        Monster.update(self, time, player, monsters)
        
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class BossBot1(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 1.1 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 6
        self.curHp = 6 
        self.animatedSprite = AnimationSprite('bossBots', 0)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 100)
        self.damagePlayerOnTouch = True
        self.fireTimeout = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
            
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 75)
            self.body.apply_impulse((random.choice([-1000, 0, 1000]),random.randint(0, 1000)), (0,0))
        self.fireTimeout -= time
        if self.fireTimeout < 0:
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + 32, position[1]), (7000, 7000)))
            self.projectilesToFire.append(EnemyEnergyBall((position[0] - 32, position[1]), (-7000, 7000)))
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.jetPackParticleToAddTimeOut = 30
            numToEmit = random.randint(1, 5)
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            for i in range(numToEmit):
                self.particlesToEmit.append(FlyBotParticle([random.choice([position[0] + 12, position[0] + 20]), position[1] + 30]))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])

class BossBot2(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 1.1 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 6
        self.curHp = 6 
        self.animatedSprite = AnimationSprite('bossBots', 1)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 100)
        self.damagePlayerOnTouch = True
        self.fireTimeout = 1000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
            
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 100)
            self.body.apply_impulse((random.choice([-1000, 0, 1000]),random.randint(-1000, 1000)), (0,0))
        self.fireTimeout -= time
        if self.fireTimeout < 0:
            self.fireTimeout = 500
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + 32, position[1]), (random.randint(0,7000), random.randint(0,7000))))
            self.projectilesToFire.append(EnemyEnergyBall((position[0] - 32, position[1]), (random.randint(-7000,0), random.randint(0,7000))))
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.jetPackParticleToAddTimeOut = 30
            numToEmit = random.randint(1, 5)
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            for i in range(numToEmit):
                self.particlesToEmit.append(FlyBotParticle([random.choice([position[0] + 12, position[0] + 20]), position[1] + 30]))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])
        
class BossBot3(Monster):
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedBody.apply_force((0, -constants.worldGrav * 1.1 * mass))
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Monster.__init__(self, uninitializedBody, uninitializedShape)
        self.maxHp = 10
        self.curHp = 10
        self.animatedSprite = AnimationSprite('bossBots', 2)
        self.animationTimer = random.randint(0, constants.animationFrameTimeOut)
        self.animationFrame = random.randint(0, 3)
        self.forceTimer = random.randint(0, 100)
        self.damagePlayerOnTouch = True
        self.fireTimeout = 2000
        self.jetPackParticleToAddTimeOut = 30
        self.deathSound = 'explode'
    
    def addDeathParticles(self):
        numToEmit = 40
        v = self.body.position
        position = int(v[0]), int(v[1])
        for i in range(numToEmit):
            self.particlesToEmit.append(ExplosionParticle([random.randint(position[0] + 12, position[0] + 20), random.randint(position[1] + 12, position[1] + 20)]))
                
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        p2 = rot.x * r * 0.9, -rot[1] * r * 0.9
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
    
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def update(self, time, player, monsters):
        self.animationTimer -= time
        if self.animationTimer < 0:
            self.animationTimer = constants.animationFrameTimeOut
            self.animationFrame += 1
            if self.animationFrame >= 4:
                self.animationFrame = 0
        self.forceTimer -= time
        if self.forceTimer < 0:
            self.forceTimer =  random.randint(0, 100)
            self.body.apply_impulse((random.choice([-1000, 0, 1000]),random.randint(-1000, 1000)), (0,0))
        self.fireTimeout -= time
        if self.fireTimeout < 0:
            self.fireTimeout = 2000
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            self.projectilesToFire.append(EnemyEnergyBall((position[0] + 32, position[1]), (7000, 7000)))
            self.projectilesToFire.append(EnemyEnergyBall((position[0] - 32, position[1]), (-7000, 7000)))
        self.jetPackParticleToAddTimeOut -= time
        if self.jetPackParticleToAddTimeOut < 0:
            self.jetPackParticleToAddTimeOut = 30
            numToEmit = random.randint(1, 5)
            r = self.shape.radius
            v = self.body.position
            rot = self.body.rotation_vector
            position = int(v[0]), int(v[1])
            for i in range(numToEmit):
                self.particlesToEmit.append(FlyBotParticle([random.choice([position[0] + 12, position[0] + 20]), position[1] + 30]))
        Monster.update(self, time, player, monsters)
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0] - 16, pos[1] - 16])