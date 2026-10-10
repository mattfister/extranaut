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
## How far a threshold's tint moves toward the zones it borders.
THRESHOLD_TINT = 0.5

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
        beyond = {d: worldmap.ZONES[z] for d, z in worldmap.borders(world, at).items()}
        dressed = decor.decorate(
            built.rows, built.monsters, built.player_start, zone, world.kind[at], at, sheets,
            random.Random(room_seed * DECOR_SEED), beyond,
        )
        tint = zone["tint"]
        if world.kind[at] == "threshold":
            tint = _blend(tint, [other["tint"] for _, other in sorted(beyond.items())])
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
            "tint": tint,
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


def _blend(tint, others):
    """A tint part of the way to the average of some others."""
    return [
        round(own + (sum(other[i] for other in others) / len(others) - own) * THRESHOLD_TINT, 3)
        for i, own in enumerate(tint)
    ]


def main():
    world = generate()
    with open(JSON_PATH, "w", newline="\n") as file:
        json.dump(world, file, separators=(",", ":"))
    print("wrote %s: %d rooms" % (JSON_PATH.relative_to(ROOT).as_posix(), len(world["rooms"])))


if __name__ == "__main__":
    main()
