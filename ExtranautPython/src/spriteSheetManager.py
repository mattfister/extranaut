import pygame
import os
import glob

from pygame.locals import *
from spriteSheet import *

spriteSheets = {}

class SpriteSheetManager:
   def __init__(self):
      pass
      
   def load(self):
      path = os.path.join("../graphics/sprites/")
      fileNameList = map(lambda x:x[len(path):-4], 
                         glob.glob(os.path.join(path,"*.png")))
      
      for name in fileNameList:
         fullname = os.path.abspath( path )
         fullname = os.path.join( fullname, name+'.png' )
                  
         image = pygame.image.load( fullname ).convert_alpha()
         spriteSheet = SpriteSheet(pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2)), name)
         spriteSheets[name] = spriteSheet
