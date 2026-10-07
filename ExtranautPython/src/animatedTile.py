import animationSprite
import constants

class AnimatedTile:
    def __init__(self, animationSprite, pos):
        self.animationSprite = animationSprite
        self.pos = pos
        self.frameNum = 0
        self.numFrames = self.animationSprite.getNumFrames()
        self.timeOut = constants.animationFrameTimeOut
        
    def draw(self, screen, camera):
        screen.blit(self.animationSprite.getFrame(self.frameNum), (self.pos[0] + camera[0], self.pos[1] + camera[1]))
    
    def update(self, time):
        self.timeOut -= time
        if self.timeOut < 0:
            self.frameNum += 1
            if self.frameNum >= self.numFrames:
                self.frameNum = 0
            self.timeOut = constants.animationFrameTimeOut
    