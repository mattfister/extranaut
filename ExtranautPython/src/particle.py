import math
import constants
import copy
from animationSprite import *
import pygame
import random
class Particle():
    def __init__(self, pos, vel, acc, fric, rot, rotVel, rotAcc, rotFric, lifeTime, animationName, animationSheetRowNum, numFrames):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        self.fric = fric
        
        self.rot = rot
        self.rotVel = rotVel
        self.rotAcc = rotAcc
        self.rotFric = rotFric
        
        self.lifeTime = lifeTime
        self.animationName = animationName
        self.dead = False
        self.keep = False
        self.animatedSprite = AnimationSprite(animationName, animationSheetRowNum)
        self.animationFrame = 0
        self.animationTimeOut = 60
        self.numFrames = numFrames
        
    def update(self, time):
        self.lifeTime -= time
        if self.lifeTime <= 0:
            self.dead = True
        
        self.animationTimeOut -= time
        if self.animationTimeOut <= 0:
            self.animationTimeOut = 60
            self.animationFrame += 1
            if self.animationFrame >= self.numFrames:
                self.animationFrame = 0
        
        self.vel[0] = self.vel[0] + self.acc[0] * time
        self.vel[1] = self.vel[1] + self.acc[1] * time
        
        if self.vel[0] > 0:
            self.vel[0] = self.vel[0] - self.fric * time
            if self.vel[0] < 0:
                self.vel[0] = 0
        
        if self.vel[0] < 0:
            self.vel[0] = self.vel[0] + self.fric * time
            if self.vel[0] > 0:
                self.vel[0] = 0
                
        if self.vel[1] > 0:
            self.vel[1] = self.vel[1] - self.fric * time
            if self.vel[1] < 0:
                self.vel[1] = 0
        
        if self.vel[1] < 0:
            self.vel[1] = self.vel[1] + self.fric * time
            if self.vel[1] > 0:
                self.vel[1] = 0
        
        self.pos[0] = self.pos[0] + self.vel[0] * time
        self.pos[1] = self.pos[1] + self.vel[1] * time
        
        self.rot = self.rot + self.rotVel * time
        self.rotVel = self.rotVel + self.rotAcc * time
        
        if self.rotVel > 0:
            self.rotVel = self.rotVel - self.rotFric * time
            if self.rotVel < 0:
                self.rotVel = 0
                
        if self.rotVel < 0:
            self.rotVel = self.rotVel + self.rotFric * time
            if self.rotVel > 0:
                self.rotVel = 0
    
    def draw(self, screen, camera):
        image = self.animatedSprite.getFrame(self.animationFrame)
        imageRot = pygame.transform.rotate(image, math.degrees(self.rot))
        newCenter = imageRot.get_rect().center
        screen.blit(imageRot, (self.pos[0] + camera[0] - newCenter[0], self.pos[1] + camera[1] - newCenter[1]))

class FlyBotParticle(Particle):
    def __init__(self, pos):
        Particle.__init__(self, pos, [random.uniform(-0.01, 0.01), random.uniform(.05, .1)], [0, 0], 0, 0, 0, 0, 0, random.randint(200, 300), 'botParticles', 0, 4)
         
class JetPackFireParticle(Particle):
    def __init__(self, pos):
        Particle.__init__(self, pos, [random.uniform(-0.1, 0.1), random.uniform(.05, .1)], [0, 0], 0, 0, 0, 0, 0, random.randint(800, 1500), 'jetPackParticles', 0, 4)


class ExplosionParticle(Particle):
    def __init__(self, pos):
        Particle.__init__(self, pos, [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)], [0, 0], 0, 0, 0, 0, 0, random.randint(800, 1500), 'botParticles', 0, 4)

class JetPackSmokeParticle(Particle):
    def __init__(self, pos):
        Particle.__init__(self, pos, [random.uniform(-0.1, 0.1), random.uniform(-.1, .1)], [0, 0], .0001, 0, 0, 0, 0, random.randint(800, 1500), 'jetPackParticles', 2, 4)

class EnergyBallParticle(Particle):
    def __init__(self, pos):
        Particle.__init__(self, pos, [random.uniform(-0.1, 0.1), random.uniform(-.1, .1)], [0, 0], 0, 0, 0, 0, 0, random.randint(400, 600), 'jetPackParticles', 3, 4)
        