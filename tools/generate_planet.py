"""Generate Planet Korvax, a second campaign built from Zorta's parts.

Writes tools/korvax.json in the format of tools/zorta.json, for
tools/import_world.gd. The seed is fixed, so every run writes the same file.

Usage: python tools/generate_planet.py
"""
import json
import random
import struct
import zlib
from pathlib import Path

from planet_gen import render, room, worldmap

SEED = 2026
SRC_TILE = 16
FINAL_STRETCH_MUSIC = "fallenExtranaut"
BOSS_MUSIC = "bossBattle"

ROOT = Path(__file__).resolve().parent.parent
ZORTA_PATH = ROOT / "tools" / "zorta.json"
JSON_PATH = ROOT / "tools" / "korvax.json"

_alpha_cache = {}


def _alpha(sheet):
    """A tile sheet's alpha channel, as rows of bytes. Reads 8-bit RGBA PNGs
    without interlacing, which is what every tile sheet is."""
    if sheet in _alpha_cache:
        return _alpha_cache[sheet]
    data = (ROOT / "assets" / "sprites" / (sheet + ".png")).read_bytes()
    pos, packed, header = 8, b"", None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            packed += body
        pos += 12 + length
    width, height, depth, colour, _, _, interlace = header
    if (depth, colour, interlace) != (8, 6, 0):
        raise ValueError("%s.png is not a plain 8-bit RGBA image" % sheet)
    raw = zlib.decompress(packed)
    stride = width * 4
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        mode, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = line[i - 4] if i >= 4 else 0
            b = previous[i]
            c = previous[i - 4] if i >= 4 else 0
            if mode == 1:
                line[i] = (line[i] + a) & 255
            elif mode == 2:
                line[i] = (line[i] + b) & 255
            elif mode == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif mode == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line[3::4]))
        previous = line
    _alpha_cache[sheet] = rows
    return rows


def tile_is_blank(sheet, tx, ty):
    """Whether a 16 px tile of a sheet is missing or fully transparent."""
    rows = _alpha(sheet)
    if (ty + 1) * SRC_TILE > len(rows) or (tx + 1) * SRC_TILE > len(rows[0]):
        return True
    return not any(
        any(rows[y][tx * SRC_TILE:(tx + 1) * SRC_TILE])
        for y in range(ty * SRC_TILE, (ty + 1) * SRC_TILE)
    )


def generate(seed=SEED):
    zorta = json.loads(ZORTA_PATH.read_text())
    sheets = zorta["sheets"]
    world = worldmap.build(random.Random(seed))
    rooms = []
    for at in sorted(world.links):
        zone = worldmap.ZONES[world.zone[at]]
        midground, backdrop, music = zone["midground"], zone["background"], zone["music"]
        slopes = not any(tile_is_blank(midground, *tile) for tile in render.SLOPE_TILES.values())
        built = room.build(world, at, seed * 100 + at[0] * 10 + at[1], slopes)
        if world.kind[at] == "boss":
            music = BOSS_MUSIC
        elif at in world.behind_gate:
            music = FINAL_STRETCH_MUSIC
        hole = None if built.hole is None else (built.hole, built.hole + 2)
        rooms.append({
            "x": at[0],
            "y": at[1],
            "music": music,
            "player_start": built.player_start,
            "layers": {
                "background": render.background(sheets.index(backdrop)),
                "midground": render.tiles(built.rows, sheets.index(midground)),
                "foreground": [],
            },
            "animated": [],
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
