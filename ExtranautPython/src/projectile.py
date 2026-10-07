import pymunk
import pygame
import copy
import spriteSheetManager
from animationSprite import *
import math
import constants
import random
from pymunkShims import *
from particle import *

class Projectile():
    def __init__(self, body, shape):
        self.body = body
        self.shape = shape
        self.ballistic = True
        self.initialImpulse = (0,0)
        self.damageMonsters = False
        self.dead = False
        self.lifeTime = 5000
        self.particlesToEmit = []
        
    def draw(self, screen, camera):
        pass
    
    def initialize(self, space):
        if self.ballistic == False:
            self.body.apply_force((0, -constants.worldGrav * self.body.mass))
        self.body.apply_impulse(self.initialImpulse)
        space.add(self.body, self.shape)
        
    def uninitialize(self):
        self.body = None
        self.shape = None
    
    def drawStatic(self):
        pass
    
    def isDead(self):
        return self.dead
    
    def handleCollision(self, selfShape, collisionShape, contacts):
        if isinstance(collisionShape, ObjectCircle):
            if isinstance(collisionShape.object, Projectile):
                if self.damageMonsters != collisionShape.object.damageMonsters:
                    self.dead = True
            else:
                self.dead = True
        else: # it's a wall
            self.dead = True
    
class EnergyBall(Projectile):
    def __init__(self, position, initialImpulse):
        radius = 8
        mass = 20
        moment = pymunk.inf
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        uninitializedShape.group = constants.playerGroup
        Projectile.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('projectiles1', 0)
        self.animationFrame = 0
        self.animationTimeOut = 60
        self.ballistic = False
        self.damageMonsters = True
        self.initialImpulse = initialImpulse
        self.emitProjectilesTimeOut = 30
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0], pos[1]])
        
    def update(self, time):
        if abs(self.body._get_velocity()) < 400:
            self.dead = True
        self.animationTimeOut -= time
        if self.animationTimeOut <= 0:
            self.animationFrame += 1
            if self.animationFrame > 3:
                self.animationFrame = 0
            self.animationTimeOut = 60
            
    def getScreenPosition(self, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        image = self.animatedSprite.getFrame(0)
        return (int(p[0] - image.get_rect().center[0] + camera[0]), int(p[1] - image.get_rect().center[1] + camera[1]))

class EnemyEnergyBall(Projectile):
    def __init__(self, position, initialImpulse):
        radius = 8
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Projectile.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('projectiles1', 1)
        self.animationFrame = 0
        self.animationTimeOut = 60
        self.ballistic = False
        self.damageMonsters = False
        self.initialImpulse = initialImpulse
        self.emitProjectilesTimeOut = 30
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0], pos[1]])
        
    def update(self, time):
        self.animationTimeOut -= time
        if self.animationTimeOut <= 0:
            self.animationFrame += 1
            if self.animationFrame > 3:
                self.animationFrame = 0
            self.animationTimeOut = 60
            
    def getScreenPosition(self, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        image = self.animatedSprite.getFrame(0)
        return (int(p[0] - image.get_rect().center[0] + camera[0]), int(p[1] - image.get_rect().center[1] + camera[1]))



class EnergyGrenade(Projectile):
    def __init__(self, position, initialImpulse):
        radius = 8
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.setObject(self)
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        Projectile.__init__(self, uninitializedBody, uninitializedShape)
        self.animatedSprite = AnimationSprite('projectiles2', 0)
        self.animationFrame = 0
        self.animationTimeOut = 60
        self.ballistic = True
        self.damageMonsters = False
        self.initialImpulse = initialImpulse
        self.emitProjectilesTimeOut = 30
        self.dying = False
        self.deathTimer = 3000
        
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        
        image = self.animatedSprite.getFrame(self.animationFrame)
        
        oldCenter = p
        rotImage = pygame.transform.rotate(image, math.degrees(-self.body.angle))
        screen.blit(rotImage, [int(p[0] - rotImage.get_rect().center[0] + camera[0]), int(p[1] - rotImage.get_rect().center[1] + camera[1])])
    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0], pos[1]])
        
    def update(self, time):
        self.animationTimeOut -= time
        if self.animationTimeOut <= 0:
            self.animationFrame += 1
            if self.animationFrame > 3:
                self.animationFrame = 0
            self.animationTimeOut = 60
        if self.dying:
            self.deathTimer -= time
            if self.deathTimer <= 0:
                self.dead = True
                numToEmit = random.randint(10, 20)
                for i in range(numToEmit):
                    self.particlesToEmit.append(EnergyBallParticle([self.getScreenPosition([0,0])[0] + 32, self.getScreenPosition([0,0])[1] + 24]))

            
            
    def getScreenPosition(self, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        image = self.animatedSprite.getFrame(0)
        return (int(p[0] - image.get_rect().center[0] + camera[0]), int(p[1] - image.get_rect().center[1] + camera[1]))
        
    def handleCollision(self, selfShape, collisionShape, contacts):
        if isinstance(collisionShape, ObjectCircle):
            if not isinstance(collisionShape.object, Projectile):
                self.dead = True
            else:
                if self.damageMonsters != collisionShape.object.damageMonsters:
                    if self.dead == False:
                        numToEmit = random.randint(10, 20)
                        for i in range(numToEmit):
                            self.particlesToEmit.append(EnergyBallParticle([self.getScreenPosition([0,0])[0] + 32, self.getScreenPosition([0,0])[1] + 24]))
                        self.dead = True
                    
        else: # it's a wall
            self.dying = True
            