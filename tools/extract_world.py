"""Convert the original Extranaut world pickle to JSON for the Godot importer.

The pickle was written by Python 2 and references the game's own classes and
pygame. Stub classes stand in for all of them, so nothing but the standard
library is needed.

Usage: python tools/extract_world.py
"""
import json
import pickle
from pathlib import Path

TILE = 32
ROOM_TILES_X = 30
ROOM_TILES_Y = 24
LAYERS = ("background", "midground", "foreground")

ROOT = Path(__file__).resolve().parent.parent
PICKLE_PATH = ROOT / "ExtranautPython" / "data" / "zorta.xn0"
JSON_PATH = ROOT / "tools" / "zorta.json"


class _Stub:
    def __init__(self, *args, **kwargs):
        pass

    def __setstate__(self, state):
        self.__dict__.update(state)


class _Unpickler(pickle.Unpickler):
    def __init__(self, file):
        super().__init__(file, encoding="latin1")
        self._classes = {}

    def find_class(self, module, name):
        key = (module, name)
        if key not in self._classes:
            self._classes[key] = type(name, (_Stub,), {})
        return self._classes[key]


def load_planet(path):
    with open(path, "rb") as file:
        return _Unpickler(file).load()


def _sheet_names(planet):
    names = set()
    for column in planet.rooms:
        for room in column:
            for layer in LAYERS:
                for tile in getattr(room, layer + "Tiles"):
                    names.add(tile.sheetSprite.spriteSheetName)
    return sorted(names)


def _convert_layer(tiles, sheet_index):
    converted = []
    for tile in tiles:
        tx = tile.pos[0] // TILE
        ty = tile.pos[1] // TILE
        if not (0 <= tx < ROOM_TILES_X and 0 <= ty < ROOM_TILES_Y):
            continue
        rect = tile.sheetSprite.rect
        converted.append(
            [tx, ty, sheet_index[tile.sheetSprite.spriteSheetName], rect[0] // TILE, rect[1] // TILE]
        )
    return converted


def _convert_room(room, x, y, sheet_index):
    animated = []
    for layer in LAYERS:
        for tile in getattr(room, "animated" + layer.capitalize() + "Tiles"):
            animated.append(
                {
                    "layer": layer,
                    "sheet": tile.animationSprite.animationSheetName,
                    "row": tile.animationSprite.row,
                    "pos": [int(tile.pos[0]), int(tile.pos[1])],
                }
            )
    start = room.playerTestPosition
    return {
        "x": x,
        "y": y,
        "music": room.music,
        "player_start": None if start is None else [int(start[0]), int(start[1])],
        "layers": {
            layer: _convert_layer(getattr(room, layer + "Tiles"), sheet_index) for layer in LAYERS
        },
        "animated": animated,
        "walls": [
            [int(a[0]), int(a[1]), int(b[0]), int(b[1])] for a, b in room.uninitializedWallSegments
        ],
        "monsters": [
            [cls.__name__, int(pos[0]), int(pos[1])] for cls, pos in room.uninitializedMonsters
        ],
    }


def convert(planet):
    sheets = _sheet_names(planet)
    sheet_index = {name: i for i, name in enumerate(sheets)}
    rooms = []
    for x, column in enumerate(planet.rooms):
        for y, room in enumerate(column):
            rooms.append(_convert_room(room, x, y, sheet_index))
    return {
        "start_room": list(planet.playerCheckPointRoom),
        "player": {
            "max_hp": planet.playerMaxHp,
            "max_fuel": planet.playerMaxJetpackFuel,
            "gun_level": planet.playerGunLevel,
            "artifacts": planet.playerArtifactsGathered,
        },
        "sheets": sheets,
        "rooms": rooms,
    }


def main():
    world = convert(load_planet(PICKLE_PATH))
    with open(JSON_PATH, "w", newline="\n") as file:
        json.dump(world, file, separators=(",", ":"))
    print("Wrote %s (%d rooms)" % (JSON_PATH, len(world["rooms"])))


if __name__ == "__main__":
    main()
