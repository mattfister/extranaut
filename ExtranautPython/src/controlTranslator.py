import pygame

def isUpPressed(keys, joystick):
    
    if keys[pygame.K_UP]:
        return True
    if joystick != None and joystick.get_numhats > 0:
        hat = joystick.get_hat(0)
        if hat[1] == 1:
            return True
    return False

def isDownPressed(keys, joystick):
    if keys[pygame.K_DOWN]:
        return True
    if joystick != None and joystick.get_numhats > 0:
        hat = joystick.get_hat(0)
        if hat[1] == -1:
            return True
    return False

def isLeftPressed(keys, joystick):
    if keys[pygame.K_LEFT]:
        return True
    if joystick != None and joystick.get_numhats > 0:
        hat = joystick.get_hat(0)
        if hat[0] == -1:
            return True
    return False

def isRightPressed(keys, joystick):
    if keys[pygame.K_RIGHT]:
        return True
    if joystick != None and joystick.get_numhats > 0:
        hat = joystick.get_hat(0)
        if hat[0] == 1:
            return True
    return False

def isShootPressed(keys, joystick):
    if keys[pygame.K_z] or keys[pygame.K_SPACE] or keys[pygame.K_LCTRL]:
        return True
    if joystick != None:
        if joystick.get_numbuttons > 0:
            if joystick.get_button(0):
                return True
    return False