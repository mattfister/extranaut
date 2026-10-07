import random

class ParticleSystem():
    def __init__(self):
        self.particles = []
        
    def update(self, time):
        newParticles = []
        for particle in self.particles:
            particle.update(time)
            if particle.dead == False or particle.keep == True:
                newParticles.append(particle)
        self.particles = newParticles
        
    def draw(self, screen, offset):
        for particle in self.particles:
            particle.draw(screen, offset)

    def addParticles(self, particleList, pos, amount):
        for num in range(amount):
            newParticle = random.choice(particleList)(pos)
            self.particles.append(newParticle)
    
    def addParticle(self, particle):
        self.particles.append(particle)
        
    def clear(self):
        self.particles = []