"""Generate Planet Korvax, a second campaign built from Zorta's parts.

Writes tools/korvax.json in the format of tools/zorta.json, for
tools/import_world.gd. The seed is fixed, so every run writes the same file.

Usage: python tools/generate_planet.py
"""
import json
import random
from pathlib import Path

from planet_gen import decor, render, room, worldmap
from planet_gen.sheets import tile_is_blank

SEED = 2026
## Decorations draw from their own random stream, so changing them never
## changes a room's shape or its monsters.
DECOR_SEED = 7919
FINAL_BOSS_MUSIC = "fallenExtranaut"
BOSS_MUSIC = "bossBattle"

ROOT = Path(__file__).resolve().parent.parent
ZORTA_PATH = ROOT / "tools" / "zorta.json"
JSON_PATH = ROOT / "tools" / "korvax.json"

def generate(seed=SEED):
    zorta = json.loads(ZORTA_PATH.read_text())
    sheets = zorta["sheets"]
    world = worldmap.build(random.Random(seed))
    rooms = []
    for at in sorted(world.links):
        zone = worldmap.ZONES[world.zone[at]]
        midground, music = zone["midground"], zone["music"]
        slopes = not any(tile_is_blank(midground, *tile) for tile in render.SLOPE_TILES.values())
        room_seed = seed * 100 + at[0] * 10 + at[1]
        built = room.build(world, at, room_seed, slopes)
        dressed = decor.decorate(
            built.rows, built.monsters, built.player_start, zone, world.kind[at], at, sheets,
            random.Random(room_seed * DECOR_SEED),
        )
        if world.kind[at] == "boss":
            music = BOSS_MUSIC
        elif world.kind[at] == "final":
            music = FINAL_BOSS_MUSIC
        hole = None if built.hole is None else (built.hole, built.hole + 2)
        rooms.append({
            "x": at[0],
            "y": at[1],
            "music": music,
            "player_start": built.player_start,
            "layers": dressed.layers(),
            "animated": dressed.animated,
            "walls": render.walls(built.rows, hole),
            "monsters": built.monsters,
            "tint": zone["tint"],
            "zone": zone["name"],
            "cells": built.rows,
            "links": dict(sorted(world.links[at].items())),
            "kind": world.kind[at],
        })
    return {
        "start_room": list(worldmap.START),
        "player": zorta["player"],
        "sheets": sheets,
        "rooms": rooms,
    }


def main():
    world = generate()
    with open(JSON_PATH, "w", newline="\n") as file:
        json.dump(world, file, separators=(",", ":"))
    print("wrote %s: %d rooms" % (JSON_PATH.relative_to(ROOT).as_posix(), len(world["rooms"])))


if __name__ == "__main__":
    main()
