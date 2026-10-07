import pygame
import os
import glob

from pygame.locals import *
from animationSheet import *

animationSheets = {}

class AnimationSheetManager:
   def __init__(self):
      pass
      
   def load(self):
      path = os.path.join("../graphics/animations/")
      fileNameList = map(lambda x:x[len(path):-4], 
                         glob.glob(os.path.join(path,"*.png")))
      
      for name in fileNameList:
         fullname = os.path.abspath( path )
         fullname = os.path.join( fullname, name+'.png' )
                  
         image = pygame.image.load( fullname ).convert_alpha()
         animationSheet = AnimationSheet(pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2)), name)
         animationSheets[name] = animationSheet
