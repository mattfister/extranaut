import pymunk
import pygame
import copy
import spriteSheetManager
from animationSprite import *
import math
import constants
import random
from projectile import *
from pymunkShims import *
from monster import *
from particle import *
import controlTranslator
from sheetSprite import *
import sounds

class PlayerCharacter():
    def __init__(self, position):
        radius = 16
        mass = 20
        moment = pymunk.moment_for_circle(mass, radius, 0.0, (0,0))
        
        uninitializedBody = pymunk.Body(mass, moment)
        uninitializedBody.position = position
        uninitializedShape = ObjectCircle(uninitializedBody, radius, (0,0))
        uninitializedShape.object = self
        uninitializedShape.friction = .5
        uninitializedShape.collision_type = 0
        self.body = uninitializedBody
        self.shape = uninitializedShape
        self.shape.group = constants.playerGroup
        self.animatedSpriteRight = AnimationSprite('xenoNaturalistSheet', 0)
        self.animatedSpriteLeft = AnimationSprite('xenoNaturalistSheet', 1)
        self.animatedSpriteDeadRight = AnimationSprite('xenoNaturalistSheet', 2)
        self.animatedSpriteDeadLeft = AnimationSprite('xenoNaturalistSheet', 3)
        self.transitioning = False
        self.projectilesToFire = []
        self.shootTimeOut = 0
        self.facingRight = 1
        self.animationTimeOut = 60
        self.animationFrame = 0
        self.onGround = False
        self.onGroundTimeout = 30
        self.maxJetPackFuel = 1000
        self.hitSound = 'hit'
        self.jetPackFuel = copy.copy(self.maxJetPackFuel)
        self.hitTimeOut = 0
        self.hitFlash = 30
        self.maxHp = 5
        self.curHp = self.maxHp
        
        self.particlesToEmit = []
        
        self.jetPackParticleToAddTimeOut = 30
        self.jetPackImpulseTimeOut = 100
        self.jetPackFuelAddTimeOut = 40
        
        self.gunLevel = 1
        
        self.artifactsFound = 0
        self.deathTimer = 5000
        
    def isDead(self):
        return self.curHp <= 0 and self.deathTimer <= 0
    
    def hit(self):
        if self.hitTimeOut > 0:
            return
        else:
            sounds.playEffect(self.hitSound)
            self.curHp -= 1
            self.hitTimeOut = 1000
            self.hitFlash = 30
            
    def handleCollision(self, selfShape, collisionShape, contacts):
        for contact in contacts:
            contactPositionBodyY = contact.position[1] - self.getScreenPosition((0,0))[1]
            if contactPositionBodyY > 28:
                self.onGround = True
                self.onGroundTimeout = 30
        if isinstance(collisionShape, ObjectCircle):
            if isinstance(collisionShape.object, Monster):
                if collisionShape.object.damagePlayerOnTouch:
                    self.hit()
                if collisionShape.object.isPowerup:
                    collisionShape.object.applyPowerup(self)
            if isinstance(collisionShape.object, Projectile):
                self.hit()
                
    def draw(self, screen, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        if self.curHp <= 0:
            if self.facingRight:
                image = self.animatedSpriteDeadRight.getFrame(0)
                screen.blit(image, self.getScreenPosition(camera))
            else:
                image = self.animatedSpriteDeadLeft.getFrame(0)
                screen.blit(image, self.getScreenPosition(camera))
        elif self.hitTimeOut <= 0 or self.hitFlash < 0:
            if self.facingRight:
                image = self.animatedSpriteRight.getFrame(self.animationFrame)
                screen.blit(image, self.getScreenPosition(camera))
            else:
                image = self.animatedSpriteLeft.getFrame(self.animationFrame)
                screen.blit(image, self.getScreenPosition(camera))
    
    def drawHpBar(self, screen):
        xPos = constants.tileSize * constants.roomSizeX
        yPos = constants.resolution[1] - constants.tileSize
        image = SheetSprite('bars', [0, 0, constants.tileSize, constants.tileSize])
        if self.curHp > 0:
            for i in range(self.curHp):
                screen.blit(image.getImage(), [xPos, yPos])
                yPos -= constants.tileSize
                
    def drawFuelBar(self, screen):
        xPos = constants.tileSize * (constants.roomSizeX + 1)
        yPos = constants.resolution[1] - constants.tileSize
        image = SheetSprite('bars', [constants.tileSize, 0, constants.tileSize*2, constants.tileSize])
        if self.curHp > 0:
            for i in range(self.jetPackFuel/500):
                screen.blit(image.getImage(), [xPos, yPos])
                yPos -= constants.tileSize
                
    def getScreenPosition(self, camera):
        r = self.shape.radius
        v = self.body.position
        rot = self.body.rotation_vector
        p = int(v[0]), int(v[1])
        image = self.animatedSpriteRight.getFrame(0)
        return (int(p[0] - image.get_rect().center[0] + camera[0]), int(p[1] - image.get_rect().center[1] + camera[1]))
        
        
    def update(self, time, keys, joystick):
        if self.jetPackImpulseTimeOut > 0:
            self.jetPackImpulseTimeOut -= time
            if self.jetPackImpulseTimeOut < 0:
                self.jetPackImpulseTimeOut = 0
        
        if self.curHp <= 0:
            self.deathTimer -= time
        
        self.onGroundTimeout -= time
        if self.onGroundTimeout <= 0:
            self.onGround = False
            self.onGroundTimeout = 0
        
        if self.curHp <= 0:
            return
        
        if controlTranslator.isUpPressed(keys, joystick):
            if self.jetPackFuel > 300:
                if self.jetPackImpulseTimeOut <= 0:
                    self.jetPackImpulseTimeOut = 100
                    self.body.apply_impulse((0, -3500), (0,0))
                    self.jetPackFuel -= 300
                    if self.jetPackFuel < 0:
                        self.jetPackFuel = 0

            self.jetPackParticleToAddTimeOut -= time
            if self.jetPackParticleToAddTimeOut < 0:
                self.jetPackParticleToAddTimeOut = 30
                numToEmit = random.randint(1, 5)
                for i in range(numToEmit):
                    if self.jetPackFuel > 300:    
                        sounds.playEffect('jet')
                        if self.facingRight:
                            self.particlesToEmit.append(JetPackFireParticle([self.getScreenPosition([0,0])[0] + 20, self.getScreenPosition([0,0])[1] + 38]))
                        else:
                            self.particlesToEmit.append(JetPackFireParticle([self.getScreenPosition([0,0])[0] + 42 , self.getScreenPosition([0,0])[1]+ 38 ]))
                    else:
                        sounds.playEffect('packEmpty')
                        if self.facingRight:
                            self.particlesToEmit.append(JetPackSmokeParticle([self.getScreenPosition([0,0])[0] + 20, self.getScreenPosition([0,0])[1] + 38]))
                        else:
                            self.particlesToEmit.append(JetPackSmokeParticle([self.getScreenPosition([0,0])[0] + 42 , self.getScreenPosition([0,0])[1]+ 38 ]))
        if controlTranslator.isLeftPressed(keys, joystick):
            self.body._set_velocity((-200, self.body._get_velocity()[1]))
            self.facingRight = 0
        if controlTranslator.isRightPressed(keys, joystick):
            self.body._set_velocity((200,self.body._get_velocity()[1]))
            self.facingRight = 1
        if not controlTranslator.isLeftPressed(keys, joystick) and not controlTranslator.isRightPressed(keys, joystick):
            self.body._set_velocity((0, self.body._get_velocity()[1]))
        
        self.shootTimeOut -= time
        
        if controlTranslator.isShootPressed(keys, joystick):
            if self.shootTimeOut <= 0:
                sounds.playEffect('shoot')
                if self.facingRight:
                    position = (self.getScreenPosition((0,0))[0] + 36, self.getScreenPosition((0,0))[1] + 23 ) 
                    self.projectilesToFire.append(EnergyBall(position, (10000, 0)))
                else:
                    position = (self.getScreenPosition((0,0))[0] - 4, self.getScreenPosition((0,0))[1] + 23 )
                    self.projectilesToFire.append(EnergyBall(position, (-10000, 0)))
                if self.gunLevel == 1:
                    self.shootTimeOut = 1000
                elif self.gunLevel == 2:
                    self.shootTimeOut = 800
                elif self.gunLevel == 3:
                    self.shootTimeOut = 600
                elif self.gunLevel == 4:
                    self.shootTimeOut = 400
                else:
                    self.shotTimeOut = 500
        
        if abs(self.body._get_velocity()[0]) > 30:
            self.animationTimeOut -= time
            if self.animationTimeOut <= 0:
                self.animationFrame += 1
                if self.animationFrame > 3:
                    self.animationFrame = 0
                self.animationTimeOut = 60
        
        if self.hitTimeOut > 0:
            self.hitTimeOut -= time
            if self.hitTimeOut < 0:
                self.hitTimeOut = 0
                
            self.hitFlash -= time
            if self.hitFlash < -30:
                self.hitFlash = 30
        
        self.jetPackFuelAddTimeOut -= time
        if self.jetPackFuelAddTimeOut <= 0:
            self.jetPackFuel += 50
            self.jetPackFuelAddTimeOut = 40
            if self.jetPackFuel > self.maxJetPackFuel:
                self.jetPackFuel = copy.copy(self.maxJetPackFuel)
        
        if constants.cheating:
            if keys[pygame.K_F9]:
                self.gunLevel += 1
            if keys[pygame.K_F10]:
                self.maxJetPackFuel += 500
            if keys[pygame.K_F11]:
                self.maxHp += 1
                self.curHp += 1
            if keys[pygame.K_F12]:
                self.artifactsFound += 1
                    
    def drawStatic(self, screen, pos):
        image = self.animatedSprite.getFrame(0)
        screen.blit(image, [pos[0], pos[1]])
