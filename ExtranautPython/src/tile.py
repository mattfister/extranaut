class Tile:
    def __init__(self, sheetSprite, pos):
        self.sheetSprite = sheetSprite
        self.pos = pos
    
    def draw(self, screen, camera):
        screen.blit(self.sheetSprite.getImage(), (self.pos[0] + camera[0], self.pos[1] + camera[1]))
        