import pygame
import os
import glob
import time
import random
import constants
from pygame.locals import *


# path where all our sounds are.
SOUND_PATH = os.path.join("../sounds")



def get_sound_list(path = SOUND_PATH):
    """ gets a list of sound names without their path, or extension.
    """
    # load a list of sounds without path at the beginning and .ogg at the end.
    sound_list = map(lambda x:x[len(SOUND_PATH):-4], 
                     glob.glob(os.path.join(SOUND_PATH,"*.ogg")) 
                    )
    sound_list

    
    return sound_list
       

SOUND_LIST = get_sound_list()

print str(SOUND_LIST)


class SoundManager:
    """ Controls loading, mixing, and playing the sounds.
        Having seperate classes allows different groups of sounds to be 
         loaded, and unloaded from memory easily.

        Useage:
            sm = SoundManager()
            sm.play("bump")
    """


    def __init__(self):
        """
        """
        pygame.mixer.pre_init(44100,-16,2, 1024)
        # keyed by the sound name, value is a sound object.
        self.sounds = {}

        # keyed by sound name, value is the channel.
        self.chans = {}

        self._debug_level = 0
        
        self.playingMusic = (None, None, None)
        
        self.solo = None
        self.curMusic = None
        self.musicVolume = 0
        # sounds which are queued to play.
        self.queued_sounds = []

    def _debug(self, x, debug_level = 0):
        """ Used for optionally printing debug messages.
        """
        if self._debug_level > debug_level:
            print x



    def load(self, names = SOUND_LIST, path = SOUND_PATH):
        """Loads sounds."""
        sounds = self.sounds

        if not pygame.mixer:
            for name in names:
                sounds[name] = None
            return
        for name in names:
            if not sounds.has_key(name):
                fullname = os.path.join(path, name+'.ogg')
                try: 
                    sound = pygame.mixer.Sound(fullname)
                except: 
                    sound = None
                    self._debug("Error loading sound", fullname)
                sounds[name] = sound


    def _getSound(self, name):
        """ Returns a Sound object for the given name.
        """
        if not self.sounds.has_key(name):
            self.load([name])

        return self.sounds[name]



    def play( self, name, volume=[1.0, 1.0], wait = 0, music = 0, solo = 0 ):
        """ Plays the sound with the given name.
            name - of the sound.
            volume - left and right.  Ranges 0.0 - 1.0
            wait - used to control what happens if sound is allready playing:
                0 - will not wait if sound playing.  play anyway.
                1 - if there is a sound of this type playing wait for it.
                2 - if there is a sound of this type playing do not play again.
        """
        #print "playing " + str(name) + " " + str(volume) + " " + str(music) + " " + str(solo)
        if constants.soundOverride:
            return
        
        if ( solo ):
            self.solo = name
            self.pause()
            
        vol_l, vol_r = volume

        sound = self._getSound( name )
        if sound:
            # check to see if we want to do any sound queueing, and handle it.
            if wait in [1,2]:
                # check if the sound is already playing, and is busy...
                if self.chans.has_key(name) and self.chans[name].get_busy():
                    if wait == 1:
                        # sound is already playing we wait for it to finish.
                        #self.queued_sounds.append((name, volume, wait))
                        
                        return
                    elif wait == 2:
                        # not going to play sound if playing.  We do nothing.
                        return
                        
            # play the sound, and store its channel in a 
            #   dictionary, keyed by the sound name.
            self.chans[name] = sound.play()

            # if the sound did not play, start fading out a channel, and 
            #   use pygames queueing to queue up a sound on that channel.
            #if not self.chans[name]:
                # forces a channel to return. we fade that out,
                #  and enqueue our one.
            #    self.chans[name] = pygame.mixer.find_channel(1)
            #    self.chans[name].fadeout(100)
                #self.chans[name].queue(sound)

            # if we have a channel, set its volume.
            if self.chans[name]:
                self.chans[name].set_volume(vol_l, vol_r)
            if music:
               self.playingMusic = ( name, volume, wait )
            
    def stopSounds( self ):
      pygame.mixer.stop()
      self.chans = {}
      self.playingMusic = ( None, None, None )
      #self.sounds = {}
      self.queued_sounds = []

    def pause( self ):
       pygame.mixer.pause()
   
   
    def unpause( self ):
       pygame.mixer.unpause()
       
    def update(self, elapsed_time):
        """ This should be called frequently.  At least once every game tic/frame.
        """
        # if the sound for the channel is not busy we 
        for name in self.chans.keys():
            #print str(self.chans[name])
            if not str(self.chans.get(name)) == 'None':
               if not self.chans.get(name).get_busy():
                  if not name == self.playingMusic[0]:
                     del self.chans[name]
                  else:
                     del self.chans[name]
                     self.playingMusic = (None, None, None)
                  if name == self.solo:
                     #print 'unpause'
                     self.solo = None
                     self.unpause()
               #else:
        if self.playingMusic == (None, None, None):
            pass
                     #print 'appending ' + str( self.playingMusic ) 
                     #self.queued_sounds.append( self.playingMusic )
                     
        if pygame.mixer.music.get_busy() == False:
            if self.curMusic != None:
                forceMusic(self.curMusic, self.musicVolume)
                
        # copy the current queue, to the old queue.
        old_queued = self.queued_sounds

        # start a new queue.
        self.queued_sounds = []

        # Try and play any sounds from the old queue.
        #   This may queue the sounds again, if they still shouldn't be played.
        if self.solo == None:
           for snd_info in old_queued:
              name, volume, wait = snd_info
              #print str(snd_info)
              #print 'playing old queue'
              self.play(name, volume, wait)
              

sound_manager = SoundManager()

def playSound( name, volume=[1.0, 1.0], wait = 0, music = 0, solo = 0 ):
   global sound_manager
   sound_manager.play( name, volume, wait, music, solo )

def update( elapsed_time ):
   global sound_manager
   sound_manager.update( elapsed_time )
   
def jumpSound():
   global sound_manager
   sound_manager.play( random.choice(('jump1', 'jump2', 'jump3', 'jump4', 'jump5', 'jump6', 'jump7', 'jump8', 'jump9', 'jump10')), [.2, .2] )

def hitSound():
    global sound_manager
    sound_manager.play( 'enemyHit', [.2, .2])

def lifeSound():
   global sound_manager
   sound_manager.play( random.choice(('coin1', 'coin2', 'coin3', 'coin4')), [.2, .2] )
   
def killBossSound():
   global sound_manager
   sound_manager.play( random.choice(('victory1', 'victory2', 'victory3', 'victory4' )), [.2, .2] )
   
def blipSound():
   global sound_manager
   sound_manager.play( random.choice(('blip1', 'blip2', 'blip3', 'blip4')), [.2, .2] )

def walkSound():
    global sound_manager
    sound_manager.play( 'walk', [.15, .15])
    
def door1Sound():
    global sound_manager
    sound_manager.play( 'door1', [.2, .2])

def door2Sound():
    global sound_manager
    sound_manager.play( 'door2', [.2, .2])

def orbSound():
    global sound_manager
    sound_manager.play( 'orb', [.2, .2])
    
def breakSound():
    global sound_manager
    sound_manager.play( 'break', [.2, .2])
    
def clickSound():
    global sound_manager
    sound_manager.play( 'click', [.2, .2])
    
def playMusic(songName, volume = 0.1):
    global sound_manager
    if constants.soundOverride:
        return
    if songName != None and songName != sound_manager.curMusic:
        sound_manager.curMusic = songName
        sound_manager.musicVolume = volume
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.load(os.path.join("../sounds/" + songName + '.ogg'))
        pygame.mixer.music.play(-1)

def stopMusic():
    pygame.mixer.music.set_volume(0)
    global sound_manager
    sound_manager.curMusic = None
    
def forceMusic(songName, volume = 0.1):
    global sound_manager
    if songName != None:
        sound_manager.curMusic = songName
        sound_manager.musicVolume = volume
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.load(os.path.join("../sounds/" + songName + '.ogg'))
        pygame.mixer.music.play(-1)

def reward():
    global sound_manager
    
    pygame.mixer.music.load(os.path.join("../sounds/reward.ogg"))
    pygame.mixer.music.play(1)

def playEffect(soundName):
    global sound_manager
    sound_manager.play(soundName, [.2, .2])
    
def missSound():
    global sound_manager
    sound_manager.play( 'miss', [.2, .2])

def hurtSound():
    global sound_manager
    sound_manager.play( 'hurt', [.2, .2])
    
def blockSound():
    global sound_manager
    sound_manager.play( 'block', [.2, .2])
    
def deathSound():
    global sound_manager
    sound_manager.play( 'death', [.2, .2] )

def dragonHit():
    global sound_manager
    sound_manager.play('dragonHit', [.2, .2])

def coinSound():
    global sound_manager
    sound_manager.play('coin', [.2, .2])

def heartSound():
    global sound_manager
    sound_manager.play('heart', [.2, .2])
    
def dragonPunch():
    global sound_manager
    sound_manager.play('dragonPunch', [.2, .2])

def dragonFire():
    global sound_manager
    sound_manager.play('dragonFire', [.2, .2])

def snakeSpell():
    global sound_manager
    sound_manager.play('snakeSpell', [.2, .2])

