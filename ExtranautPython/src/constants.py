import pygame.font

resolution = [1024, 768]

numRoomsX = 10
numRoomsY = 10

roomSizeX = 30
roomSizeY = 24

worldGrav = 900

playerGroup = 1


titleMenuNewGameZorta1 = 1
titleMenuNewGameZorta2 = 2
titleMenuNewGameZorta3 = 3
titleMenuNewGameReturn4 = 4
titleMenuMapEditorReturn = 5
lostGame = 6
prevSpriteSheet = 7
nextSpriteSheet = 8
backgroundLayer = 9
midgroundLayer = 10
foregroundLayer = 11
fillLayer = 12
prevAnimationSheet = 13
nextAnimationSheet = 14
buildWall = 15
startSimulation = 16
stopSimulation = 17
prevMonster = 18
nextMonster = 19
saveWorld = 20
loadWorld = 21
roomUp = 22
roomDown = 23
roomLeft = 24
roomRight = 25
playerPosition = 26
popWall = 27
popMonster = 28
popAnimation = 29
toggleForegroundVisibility = 30
toggleMidgroundVisibility = 31
toggleBackgroundVisibility = 32
clearForeground = 33
clearMidGround = 34
clearBackground = 35
chaosnautReturn = 36
chasonautGameOver = 37
setMusic = 38
titleMenuLoadGame1 = 39
titleMenuLoadGame2 = 40
titleMenuLoadGame3 = 41
titleMenuDeleteGame1 = 42
titleMenuDeleteGame2 = 43
titleMenuDeleteGame3 = 44
titleMenuNewCustom1 = 45
titleMenuNewCustom2 = 46
titleMenuNewCustom3 = 47
gameStartScreenReturn1 = 48
gameStartScreenReturn2 = 49
gameOverScreenReturn = 50
quitToTitleReturn = 51
quitToDesktopReturn = 52
resumeGame = 53
introScreenReturn = 54
endingScreenReturn = 55
wonGameReturn = 56

soundOverride = False
cheating = True

cameraSpeed = (.5, .5)

animationFrameTimeOut = 90

tileSize = 32
pygame.font.init()
defaultFont = pygame.font.Font('../graphics/fonts/KARNIVOR.ttf', 13)