import os
import random
import pygame
import pygame.mouse
import pymunk
import constants
import urllib

from controller import *
from spriteSheetManager import *
from spriteSheet import *
from sounds import *

from animationSheetManager import *
import gc

def seticon(iconname):
    """
    give an iconname, a bitmap sized 32x32 pixels, black (0,0,0) will be alpha channel
    
    the windowicon will be set to the bitmap, but the black pixels will be full alpha channel
     
    can only be called once after pygame.init() and before somewindow = pygame.display.set_mode()
    """
    icon=pygame.Surface((32,32))
    icon.set_colorkey((0,0,0))#and call that color transparant
    rawicon=pygame.image.load(iconname)#must be 32x32, black is transparant
    for i in range(0,32):
        for j in range(0,32):
            icon.set_at((i,j), rawicon.get_at((i,j)))
    pygame.display.set_icon(icon)#set wind

def main():
    gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
    
    # Initialise pygame
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    
    # Set up the display
    pygame.display.set_caption("Extranaut")
    seticon('../graphics/sprites/xenoNaturalist.bmp')
    modes = pygame.display.list_modes(32)
    if not modes:
       print '32 bit graphics not supported on your device :('
    else:
       print 'Found Resolution:', modes[0]
    
    #[x, y] = modes[0]
    [x, y] = modes[0]
    if ( x < 1024 or y < 768 ):
        print 'Unable to support minimum display, trying anyway.'
        screen = pygame.display.set_mode([1024, 768], pygame.FULLSCREEN, 32)
        constants.resolution = [1024, 768]
    else:
        #screen = pygame.display.set_mode([x, y], pygame.FULLSCREEN|pygame.DOUBLEBUF, 32)
        #constants.resolution = [x, y]
        constants.resolution[0] = 1024
        constants.resolution[1] = 768
        #screen = pygame.display.set_mode([1024, 768], pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.HWSURFACE|pygame.ASYNCBLIT, 32)
        screen = pygame.display.set_mode([1024, 768], pygame.DOUBLEBUF|pygame.HWSURFACE|pygame.ASYNCBLIT, 32)
    
    pymunk.init_pymunk()
    
    spriteManager = SpriteSheetManager()
    spriteManager.load()
    
    animationSheetManager = AnimationSheetManager()
    animationSheetManager.load()
    
    messageOfTheDay = None
    
    try:
        webFile = urllib.urlopen('http://www.kindofprettyalright.com/extranaut/extranautLaunch.txt')
        messageOfTheDay = webFile.readline()
        webFile.close()
    except IOError:
        pass
    
    pygame.display.set_icon(spriteSheetManager.spriteSheets['xenoNaturalist'].getImage([0,0]))
    
    controller = Controller(screen, messageOfTheDay)
    sounds.playEffect('extranautTitle')
    
    controller.gameLoop()

#import cProfile as profile
#profile.run('main()')
main()