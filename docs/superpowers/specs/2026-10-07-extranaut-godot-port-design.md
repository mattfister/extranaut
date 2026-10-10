# Extranaut: Godot port design

Date: 2026-10-07

## Goal

Port Extranaut, a 2010 Metroidvania written in Python 2 with pygame and pymunk
(source in `ExtranautPython/`), to Godot 4.7 for publication as a web game on
itch.io.

## Scope

Included:

- The Planet Zorta campaign with three save slots.
- Chaosnaut, the single-room wave-survival mode.
- Modernisation: control and feel polish, room transitions and juice, and a
  map of explored rooms.
- Keyboard (arrows and WASD) and gamepad input.

Dropped:

- The map editor (`xenoCartographer.py`, `mapEditorWindowManager.py`).
- Custom planets loaded through a file dialog.
- The message-of-the-day web fetch.
- Quit to desktop.
- Touch controls.

Changed:

- New Game 3 starts slot 3 (the original started slot 2).
- The F9 to F12 cheat keys work in debug builds only.
- Gun level is capped at 4. The original's level 5+ branch set a misspelled
  variable, which removed the cooldown; only three gun powerups exist, so the
  branch was unreachable in the campaign.

## Source facts the design relies on

- The world is a 10x10 grid of rooms, each 30x24 tiles of 32 px (960x768).
  92 rooms have content.
- `data/zorta.xn0` is a protocol-0 Python 2 pickle. It loads in Python 3 with
  stub classes and `encoding='latin1'`.
- Collision is separate from tiles: 4,665 wall segments, 635 of them diagonal,
  all with endpoints on the 32 px grid. The roughly 81,000 tiles across three
  layers are visual only and come from 11 sprite sheets.
- Animated tiles use sheets `animations` (rows 0 and 3) and `ruinsAnimated`
  (rows 0 and 1), at 90 ms per frame.
- Every dynamic object is a pymunk circle driven by impulses, under gravity
  900. Time values in the source are milliseconds.
- Art is authored at half size and scaled 2x on load. Sprite sheet rects stored
  in the pickle are in 2x pixels.
- Monster spawns in the campaign use 25 classes: AimerTurret, AlienArtifact,
  ArtifactDoor, BallMonster, BossBot1, BossBot2, BossBot3,
  DefenseTurretVertical, FallenExtranaut, FlyBot, Flyer, FuelPowerup,
  GunPowerup, HandBot, HeadBoss, HoverBlock, HpPowerup, JumpBot, MonsterDoor,
  MonsterDoor2, OctoBoss, OrbBoss, SavePoint, SpikyBallMonster,
  SpikyHeadMonster. Chaosnaut adds ChaosBot. Beast is defined but never placed
  and is not ported.
- Room music values: gravitorZone, zortaSurface, emeraldOrbit, bossBattle,
  pyriteZone, ruinsCore, boilingPoint, fallenExtranaut, or none (keep whatever
  is playing).
- A new game starts in room (4, 2) with 5 HP, 2000 max fuel, gun level 1 and
  0 artifacts.

## Presentation

- Logical resolution 1024x768, stretch mode `canvas_items`, aspect `keep`,
  nearest-neighbour texture filtering, Compatibility renderer.
- World coordinates stay in the original pixels so masses, impulses and
  gravity port unchanged. Sprites are drawn at 2x scale.
- The room occupies the left 960x768. A 64 px HUD strip on the right shows HP
  pips, fuel pips (one per 500 fuel), artifact count and a 10x10 minimap
  (6 px per room).
- Font: `KARNIVOR.ttf`.

## Project layout

```
assets/            art, sounds, font copied from ExtranautPython
tools/             extract_world.py, import_world.gd, smoke_test.gd
world/             tileset.tres, rooms/room_X_Y.tscn (generated)
scenes/            main, title, campaign, chaosnaut, hud, pause, image_screen
entities/          player, monsters/, projectiles/, effects/
autoload/          game.gd (state and saves), audio.gd
ExtranautPython/   original source, kept for reference, with .gdignore
```

## World import

A one-time pipeline that can be re-run. Re-running overwrites generated room
scenes.

1. `tools/extract_world.py` (Python 3) unpickles `zorta.xn0` with stub classes
   and writes `tools/zorta.json`: per room, the three tile layers, animated
   tiles, wall segments, monster spawns (class name and position), music and
   `playerTestPosition`.
2. `tools/import_world.gd`, run with Godot headless, builds `world/tileset.tres`
   with one atlas source per tile sheet, then writes one scene per room.

Each room scene contains:

- `TileMapLayer` nodes `Background`, `Midground`, `Foreground`. Dynamic
  entities draw between midground and foreground, as in the original.
- Animated tile sprites on the matching layer.
- `Walls`, a `StaticBody2D` with one thin `CapsuleShape2D` (radius 0.5) per
  wall segment, friction 0.5. Segment shapes snag bodies at wall joints.
- Monster scene instances at their spawn positions.
- Exported properties on the room root: grid position, music, player start.

## Physics and entities

- Player, monsters and projectiles are `RigidBody2D` with a `CircleShape2D`
  using the original radius, mass and friction, bounce 0, and project gravity
  900. Godot's default linear and angular damping are set to 0 project-wide.
- Bodies the original gave infinite moment get `lock_rotation`. Bodies with a
  real moment rotate and draw rotated (ball monsters, grenades).
- Original anti-gravity forces become `gravity_scale`, computed as
  1 - (upward force / weight): 0 for OctoBoss, ChaosBot, HoverBlock and the
  two energy balls; -0.1 for FlyBot and BossBots; -1 for Flyer and AimerTurret
  (the turret applies its force twice, so it rises to rest against the
  ceiling); 0.8 for DefenseTurretVertical.
- Collision handling uses contact monitoring in place of the pymunk callback.
  Player shots do not collide with the player (the original collision group).
- The player and projectiles use cast-ray continuous collision detection.
- Walls drawn on room borders contain monsters and shots but never block the
  player from leaving a room, as in the original.

Monsters:

- `Monster` base script: HP, `hit()` with a 100 ms hit timeout, contact damage
  flag, projectile vulnerability flag, powerup flag, death sound, death
  particles.
- One small script per type porting its timers, impulses and firing patterns
  from `monster.py` with the original values. BossBot1 to BossBot3 share one
  script with exported parameters.
- ArtifactDoor is removed while the player holds 4 or more artifacts.
- MonsterDoor is removed when it is the only monster left in the room;
  MonsterDoor2 when two remain. The count includes every monster-class entity
  in the room, as in the original.
- SpikyHeadMonster dies when three monsters remain, as in the original.
- HeadBoss has a 2 s shield after each hit.
- Powerups apply on player contact: HP +1 max and full heal, fuel +500 max,
  gun +1 level, artifact +1. A room whose powerup is taken does not respawn
  its powerups.
- SavePoint activates when shot.
- JumpBot has 1 HP: the original set 3, then its base constructor reset it.
- Enemy shots do not collide with each other.

Projectiles: EnergyBall (player, dies below speed 400), EnemyEnergyBall, and
EnergyGrenade (ballistic, explodes 3 s after touching a wall or on contact
with a body or a player shot).

## Player

The collision radius is 13, down from the original 16, so the player fits
through one-tile (32 px) passages, which the 0.5 px wall thickness would
otherwise close. Original values kept: mass 20, run speed 200 px/s, 1 s
invulnerability after a hit with flashing, ground detection from contacts
below the body.

Polish:

- Jetpack: continuous thrust while up is held, tuned to the original pulses
  (impulse 3500 and 300 fuel per 100 ms; regeneration 50 fuel per 40 ms; thrust
  needs more than 300 fuel). At the original's 60 fps the 40 ms timer fires
  every third frame, so regeneration was effectively 1,000 fuel/s. Continuous
  rates: thrust 1,750 px/s², burn 3,000 fuel/s, regeneration 1,000 fuel/s,
  running until empty and restarting at 500 fuel. Reach per tank must match
  the original.
- Horizontal movement accelerates to 200 px/s over roughly 80 ms and
  decelerates similarly, in place of the instant set.
- Hold to fire. Cooldown by gun level: 1000, 800, 600, 400 ms. Shot impulse
  10,000 in the facing direction.
- Death: about 2 s (was 5 s) with a fade, then respawn at the checkpoint room
  with full HP.
- Tuning values are exported on the player script.

Controls:

- Move: arrows, A/D, d-pad, left stick.
- Jetpack: up arrow, W, gamepad south button.
- Fire: Z, X, Space, gamepad west button.
- Pause: P, Enter, gamepad Start.
- Ctrl and Esc are not bound, because browsers intercept them.

## Campaign flow

- Screens: title, intro image, game, ending image, title. The ending triggers
  when the player falls out of the bottom of a row-9 room.
- Title: three slots, each showing New Game or Continue and Delete; a
  Chaosnaut button; sound and fullscreen toggles.
- Room transition: when the player crosses a room edge and an adjacent room
  exists, the next room loads, the camera slides for about 0.35 s with
  gameplay frozen, and the old room is freed. Player velocity, HP, fuel and
  facing carry over. Monsters reset on re-entry.
- Saving: activating a save point or collecting a powerup saves and sets the
  checkpoint to the current room. A save point also heals to full. Respawn
  uses the checkpoint room's player start.
- Save file: `user://save_N.json` with checkpoint room, max HP, max fuel, gun
  level, artifacts, rooms with powerup taken, visited rooms.
  The file is also rewritten on entering each room so the explored map
  survives quitting; stats and checkpoint still change only at save events.
  An unreadable save is treated as an empty slot.
- Map: visited rooms, save points in visited rooms, and the current room. Shown
  in the HUD and larger on the pause screen.
- Pause menu: Resume, Quit to Title.

## Juice and audio

- Screen shake and a brief flash on player hits and explosions.
- CPU particles for jet exhaust, empty-tank smoke, bot exhaust, energy-ball
  bursts and explosions, replacing the hand-rolled particle system.
- `Audio` autoload: music crossfade between room tracks, effect playback, a
  global mute toggle. Callers reach it through the "audio" group, because
  the global name is not defined when headless test scripts are compiled. Audio starts after the first user input, as browsers
  require.
- Music by context: title `ruinsCore`, Chaosnaut `chaosNaut`, rooms per their
  data.

## Chaosnaut

- One room bounded by four walls, 40 HoverBlocks at random positions,
  replenished to 40 when destroyed.
- First wave after 2 s, then every 10 s. Wave n spawns floor(n/4)+1 ChaosBots
  at the right edge at random heights, with the `newWave` sound.
- A bot reaching the left edge wraps to the right edge and becomes angry
  (faster, different sprite).
- The player has unlimited fuel and gun level 3, starting at bottom left.
- On death: a game-over screen with wave reached and kills, and a best score
  stored in `user://`.

## Web export

- Web export preset, single-threaded, so it runs in itch.io's embed without
  cross-origin isolation headers.
- Output to `build/web/`, zipped for upload. `build/` is git-ignored.

## Verification

- The importer runs headless without errors and produces 100 room scenes.
- `tools/smoke_test.gd` loads every room scene, instantiates it, and steps
  physics for a short time, failing on any script error.
- A jetpack check confirms that maximum height from a standing start on a full
  2000-fuel tank is within 5% of the value computed from the original pulse
  model.
- The web build is opened in a browser to confirm boot, audio and save
  persistence.
- Feel tuning is judged by play-testing by the author.

## Build order

1. Importer and room scenes.
2. Player, walls and room transitions.
3. Monsters and projectiles.
4. Saves, HUD, map and menus.
5. Chaosnaut.
6. Juice.
7. Web export.
