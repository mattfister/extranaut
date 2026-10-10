# Planet Korvax: a generated second campaign

Date: 2026-10-08

## Goal

Add a second campaign planet, built entirely from the game's existing tiles,
monsters, powerups, doors, bosses and music, with a map produced by a seeded
generator. The title screen lets the player pick a planet. Zorta is labelled
"classic" and the new planet "new - 2026". Korvax rooms are generally harder
than Zorta's.

## Decisions made with the author

- Room layouts are newly generated, not remixed Zorta rooms.
- No new art. Rooms use the existing tile sheets, retinted per zone.
- The title has a planet switch; each planet has its own three save slots.
- The map is a full 10x10 grid with Zorta's progression skeleton.
- Some rooms are infested with harmless ball monsters, because they are funny.

## Planets

`world/planets.gd` is the single place that knows which planets exist. Each
entry has:

| Field | Zorta | Korvax |
|---|---|---|
| id | `zorta` | `korvax` |
| name | Planet Zorta | Planet Korvax |
| label | classic | new - 2026 |
| rooms_dir | `res://world/rooms` | `res://world/rooms_korvax` |
| world_json | `res://tools/zorta.json` | `res://tools/korvax.json` |
| save_prefix | `save_` | `save_korvax_` |
| start_room | (4, 2) | (2, 0) |

Zorta's folder and save file names do not change, so existing saves keep
working.

Consumers:

- `save/save_game.gd`: `path`, `exists`, `read`, `write` and `delete` take a
  planet id as well as a slot.
- `save/progress.gd`: a new progress starts at the planet's start room.
  `START_ROOM` is removed.
- `scenes/campaign.gd`: gains a `planet` id set before it enters the tree, and
  loads rooms from that planet's `rooms_dir`.
- `scenes/main.gd`: passes the planet from the title to saves and the
  campaign. `--planet=ID` joins `--room=X,Y` as a development option.
- Intro image, ending image and the ending trigger (falling out of a row-9
  room) are shared by both planets.

## Title screen

A planet switch sits above the slots: a left arrow button, a label reading
`Planet Zorta (classic)` or `Planet Korvax (new - 2026)`, and a right arrow
button. Switching rebuilds the three slot rows from that planet's saves.

- Empty slot: `New Game N`.
- Used slot: `Continue Game N` and `Delete Game N`.
- `new_game` and `continue_game` carry the planet id and the slot.
- The last planet chosen is remembered in `user://settings.json` and selected
  when the title next opens. A missing or unreadable file means Zorta.

## Importer changes

`tools/import_world.gd` builds every planet in the registry, each from its
`world_json` into its `rooms_dir`. The tile set is shared.

A room in the JSON may carry an optional `tint`, `[r, g, b]` with components
from 0 to 1. The importer applies it as `modulate` on the three tile layers and
the three animated-tile holders. Entities and walls are not tinted. Zorta's
JSON has no tint, so its rooms are unchanged.

## The generator

`tools/generate_planet.py`, Python 3 standard library only, writes
`tools/korvax.json` in the format of `tools/zorta.json`. It uses a fixed seed,
so every run produces the same file, and the file is committed. Generating
offline rather than at run time lets the output be validated and adjusted.

### World map

- A spanning maze over the 10x10 grid plus extra links for loops. Every room
  has content and is reachable.
- Five zones, grown from seed cells so each is contiguous. A zone fixes the
  midground sheet, the background sheet, the tint and the music. Every room
  names its zone's track, or `bossBattle` in a boss room; the audio player
  ignores a request for the track already playing.
- Midground sheets come from the five rock sheets that share one layout:
  `rocks`, `rocksBlue`, `yellowRocks`, `grayRocks`, `greenRocks`. Backgrounds
  come from `bgRocks`, `greenRocksDark`, `bgYellowRocks`, `redRocksBg` and
  `rockBg`.
- Rooms are ranked by distance from the start room along the maze. That rank
  drives difficulty and the placement of progression items.

### Progression

Zorta's counts and rules, on a different route:

- 4 alien artifacts, each in a dead-end room with one of OrbBoss, OctoBoss,
  HeadBoss and FallenExtranaut. The artifact is in a vault (see below).
- 1 artifact door on the only route to the final stretch, which ends in a
  row-9 room with an open floor. The door sits in a two-cell-high tunnel
  through a band of rock that splits its room in two.
- 3 gun, 3 HP and 6 fuel powerups, at most one powerup per room, since a room
  with a taken powerup respawns none. Gun and HP powerups are in vaults; fuel
  powerups stand in the open on a high ledge.
- 8 to 10 save points, including one in the start room: as many as it takes
  for no room to be more than six rooms from one.

Gun, HP and fuel powerups are moved into dead-end rooms of their own zone
where the zone has one free, so a side trip is rewarded. Boss rooms, which
are dead ends too, keep their artifacts.

A vault is a dead-end tunnel two cells high, plugged by a MonsterDoor2 with
the treasure behind it. MonsterDoor2 opens when two monster-class entities
remain, which here means the door and the treasure, so the vault opens when
every hostile in the room is dead. Vault rooms hold nothing unkillable and no
save point. Doors never stand between a room's openings: rooms reset on
re-entry, so a door there would trap a player returning from the far side.
- The start room has a player start and no hostile monsters.

### Room geometry

Each room is a 30x24 grid of solid and empty cells.

- Neighbouring rooms agree on where their shared opening is. Side openings are
  at least three cells tall and stand on a floor. Floor and ceiling openings
  are at least three cells wide.
- The room starts solid. Caverns are carved around each opening and joined by
  tunnels at least three cells wide, then ledges and floating platforms are
  added back.
- Collision walls are traced from the boundary between solid and empty cells,
  merged into long segments on the 32 px grid. Convex floor corners may be cut
  to 45-degree slopes.
- The whole room border is walled, openings included, which keeps monsters
  and shots in. The exit thresholds sit inside the border, so the player never
  touches it. Only the final room's floor opening is left unwalled.
- A ceiling opening has a ledge beside it within jetpack reach.

### Tiles

- Midground: each solid cell that touches an empty cell takes the matching
  edge or corner tile from the zone sheet's nine-patch at columns 1 to 3, rows
  1 to 3. Interior cells take the centre tile (2, 2). Slopes take the sheet's
  diagonal tiles.
- Background: every cell is filled from the zone's background sheet.
- No foreground tiles and no animated tiles in the first version.

### Solvability check

A grid model of the player decides what is reachable: standing on any floor
cell, walking, falling, and jetpack flight limited to the climb available from
the base 2000-fuel tank, taken as eight cells to stay well inside the real
reach of about eleven. In every room each opening must be reachable from every
other opening. A room that fails is generated again with the next seed. Fuel
powerups therefore make rooms easier and never gate progress.

The check also confirms that every powerup, artifact and save point sits where
the player can reach it.

### Monsters and difficulty

Zorta averages about four entities a room. Korvax aims for about eight
hostiles, rising with distance from the start.

- Each room has a difficulty budget set by its rank. Monsters cost points:
  cheap ones (JumpBot, Flyer, HoverBlock), mid (FlyBot, AimerTurret,
  DefenseTurretVertical, SpikyBallMonster), dear (HandBot), and elites
  (BossBot1 to BossBot3, late zones only, at most one per room).
- **Ball infestations**: about one room in eight holds 25 to 40 BallMonsters
  and little else. They are harmless. Infestation rooms are never vault
  rooms, because the door counts every monster in the room.
- Placement rules: ground monsters stand on floor cells, flyers and hover
  blocks sit in open air, aimer turrets start below a ceiling, and nothing
  hostile spawns within four cells of an opening or the player start.
- SpikyHeadMonster is not used, because its death rule depends on Zorta's
  hand-tuned monster counts.

## Zone identity and set pieces

Added after the first play-test, in which every room felt like the same mix
of enemies.

Each zone has its own roster of hostiles and its own cave shape, defined
together with its look in `worldmap.ZONES`:

| Zone | Hostiles | Caves |
|---|---|---|
| Warrens (start) | spiky balls, flyers, a few jump bots, harmless balls wandering about | rolling caves with many slopes |
| Gravitor | fly bots and flyers among hover blocks | huge open caverns with little floor |
| Pyrite | aimer and grenade turrets, some jump bots | low, wide, flat-floored caves |
| Emerald | jump bots and hand bots | broad terraces with slopes |
| Boiling point | fly bots, spiky balls, hand bots, aimer turrets; elites from rank 0.4 | tall narrow caves with many ledges |

Every room draws its hostiles from its zone's roster, boss and vault rooms
included. Elsewhere a BossBot may join from rank 0.6.

Sixteen ordinary rooms become set pieces, two of each, dealt out in this
order going deeper so the two of a kind are far apart:

- **Sanctuary**: no hostiles, a few ball monsters.
- **Honeycomb**: one great cave filled with a staggered lattice of blocks.
- **Spikes**: 10 to 14 spiky balls.
- **Shaft**: a chimney the height of the room, climbed by ledges.
- **Hover field**: a great cave holding 12 to 18 hover blocks, fly bots and
  flyers.
- **Gallery**: one long straight hall lined with 6 to 8 aimer turrets.
- **Arena**: a great cave with three hand bots and a few of the zone's own.
- **Den**: a great cave with BossBot1 and BossBot2 together.

Set pieces never hold a door, a treasure or a save point.

## Lulls: thresholds, oddities and moods

Added after a later play-test, in which the ordinary rooms all felt as hard
as each other and the borders between zones went unnoticed.

- **Thresholds**: one room at every crossing between two zones, the one on
  the deeper side unless a room serves several crossings. It is a plain
  rectangular hall holding one piece of architecture (teeth, a monolith,
  courses of slabs, or a pyramid standing or hanging) and no monsters or
  decorations. The side nearest the other zone is drawn in that zone's rock,
  with a ragged seam, and the room's tint is halfway between the two. It may
  hold a save point or a loose powerup.
- **Oddities**: six ordinary rooms, two of each, spend a quarter of their
  budget and have a strange shape. **Mirror** is a cave the same on both
  sides, **hollow** a round cave about a core of rock, and **strata** level
  galleries stacked up the room and joined at alternating ends.
- **Moods**: every remaining ordinary room scales its budget by 0.4, 0.7, 1,
  1 or 1.4, so some are lulls and some are a fight.

## Structure: four areas, then the final one

Revised to match how Zorta is won. The planet is shown to the player as
"Zorta Depths"; its id, files and saves keep the name korvax.

- The last zone in `worldmap.ZONES`, boiling point, is the final area: the
  artifact door's room and everything behind it, six to fourteen rooms.
- The other four zones share the rest of the map, each grown from a seed
  room over the bare maze so it is one connected piece of at least ten rooms.
- Each of those four zones has one boss, in the dead end deepest inside it,
  guarding that zone's artifact. Nearest zone first, the bosses are OrbBoss,
  HeadBoss, OctoBoss and, as on Zorta, the three BossBots together.
- The Fallen Extranaut is the final boss, in the final room with two BossBot1
  escorts. The way out, a hole in the floor, is in a tunnel plugged by a
  MonsterDoor, which opens when nothing else in the room is left alive.
- The room before each boss, and before the final room, has a save point.
  More are added until no room is over six from one, to a limit of 14.

Boss rooms and the final room are arenas rather than caves: one chamber
about nineteen cells wide and twelve high with a flat floor, two side ledges
and a higher centre ledge, no slopes and no other hostiles. The vault with
the artifact (or the way out) opens off the floor on the side away from the
entrance, and the player appears in the far corner from it.

The HeadBoss is the exception, because it sits on the floor and its shots
to the right die at once. Its arena is like its room on Zorta: fifteen cells
high with no ledges, the boss in the bottom right corner, and the vault, the
way in and the player at the left end. A world whose HeadBoss room is
entered from the side, or from above or below right of column 12, is
rejected.

This supersedes the earlier notes above on where bosses go, on the Fallen
Extranaut being one of four artifact guardians, and on the final room being
an ordinary room with a hole in its floor.

## Decorations

A last pass, `planet_gen/decor.py`, dresses each finished room with tiles and
animated sprites taken from the kinds of decoration Zorta uses. It has its
own random stream and only adds visuals: cells, walls and monsters are the
same with or without it. Decorations have no collision. They go in empty
cells of the midground layer, on the top edge of floors, in the background
layer, or in the foreground layer in front of the player.

| Zone | Decorations |
|---|---|
| Warrens | grass-topped floors with tufts and swaying blades, small mushrooms, the odd waterfall |
| Gravitor | windows cut in the background onto a twinkling starfield |
| Pyrite | ruin pillars, rings and blinking tablets |
| Emerald | giant mushrooms three to eight cells tall, grass, small mushrooms, waterfalls |
| Boiling point | machine panels and orbs |

The dome in the rock sheets is the ship the player arrived in, so it is not
used as scenery. Waterfalls only run from a flat stretch of ceiling to a flat
stretch of floor, where their square ends meet a straight edge, and only in
the warrens and emerald. The pulsing tile was tried as a conduit behind
boiling point rooms and dropped: it read as flashing sand.

Rooms in the top row look out on space whatever their zone. A sanctuary
always gets grass, small mushrooms and a window onto space, and a waterfall
where its zone has them.
Each decoration has a chance per room, set in `decor.ZONE_DECOR`, so some
rooms stay bare.

The swaying grass (`grass.png`) and the waterfall (`waterfall.png`) are
animation sheets from the original game that Zorta never placed.

## Testing

- `tools/test_generate_planet.py` (unittest): the output is identical across
  runs; every room is reachable on the world map; every room passes the
  solvability check; counts of artifacts, bosses, powerups, save points and
  the artifact door are right; the start room is safe; no hostile spawns near
  an opening; at least one infestation room exists; every tile and monster
  name refers to something that exists.
- `tools/smoke_test.gd` runs over every planet in the registry and checks the
  tint.
- `tools/test_save.gd`, `tools/test_campaign.gd` and `tools/test_main.gd` are
  extended: saves are separate per planet, a Korvax campaign starts in its
  start room and can cross into a neighbouring room, and the title switch
  changes which saves are shown and which planet a new game starts.

- `tools/test_korvax.gd` checks with the real physics what the generator's
  player model takes on trust: flying up through ceiling openings and landing
  in the room above, the artifact door holding until four artifacts are held,
  and the drop through the final room's floor ending the game.

Feel, difficulty balance and how the retinted rooms look are judged by the
author in play-testing. A tuning pass is expected.
