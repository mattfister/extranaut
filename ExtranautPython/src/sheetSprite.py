import spriteSheetManager
import spriteSheet

class SheetSprite():
    def __init__(self, spriteSheetName, rect):
        self.spriteSheetName = spriteSheetName
        self.rect = rect
        
    def getImage(self):
        return spriteSheetManager.spriteSheets[self.spriteSheetName].getImageAtRect(self.rect)
    