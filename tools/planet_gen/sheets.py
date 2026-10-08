"""Reads the art, to check that a tile the generator wants really exists."""
import struct
import zlib
from pathlib import Path

SRC_TILE = 16
ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"

_alpha_cache = {}


def _alpha(folder, sheet):
    """An image's alpha channel, as rows of bytes. Reads 8-bit RGBA PNGs
    without interlacing, which is what every tile sheet is."""
    key = (folder, sheet)
    if key in _alpha_cache:
        return _alpha_cache[key]
    data = (ASSETS / folder / (sheet + ".png")).read_bytes()
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
    _alpha_cache[key] = rows
    return rows


def tile_is_blank(sheet, tx, ty, folder="sprites"):
    """Whether a 16 px tile of a sheet is missing or fully transparent."""
    rows = _alpha(folder, sheet)
    if (ty + 1) * SRC_TILE > len(rows) or (tx + 1) * SRC_TILE > len(rows[0]):
        return True
    return not any(
        any(rows[y][tx * SRC_TILE:(tx + 1) * SRC_TILE])
        for y in range(ty * SRC_TILE, (ty + 1) * SRC_TILE)
    )


def has_tiles(sheet, tiles):
    return not any(tile_is_blank(sheet, tx, ty) for tx, ty in tiles)


def animation_rows(sheet):
    """How many 16 px rows an animation sheet has."""
    return len(_alpha("animations", sheet)) // SRC_TILE
