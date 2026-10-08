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
