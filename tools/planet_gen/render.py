"""Turns a room's cells into collision walls and tiles."""
from .reach import W, H

TILE = 32
SLOPE_TILES = {"/": (2, 5), "\\": (4, 5)}
## Which side of a slope cell is its low, open side.
SLOPE_LOW_SIDE = {"/": -1, "\\": 1}
FILL_TILE = (2, 2)


def _solid(rows, x, y):
    """Cells outside the room count as rock."""
    return not (0 <= x < W and 0 <= y < H) or rows[y][x] != "."


def _merge(edges):
    """Joins unit edges, given as (line, start) pairs, into (line, start,
    end) runs."""
    runs = []
    for line, start in sorted(edges):
        if runs and runs[-1][0] == line and runs[-1][2] == start:
            runs[-1][2] = start + 1
        else:
            runs.append([line, start, start + 1])
    return runs


def walls(rows, open_floor=None):
    """Wall segments in pixels, as [x1, y1, x2, y2]: the boundary between
    rock and air, one diagonal per slope, and the room border. open_floor is
    the (first, last) column of a hole the border leaves open."""
    horizontal, vertical, segments = [], [], []
    for y in range(H):
        for x in range(W):
            char = rows[y][x]
            if char == ".":
                continue
            low_side = SLOPE_LOW_SIDE.get(char, 0)
            if char == "/":
                segments.append([x * TILE, (y + 1) * TILE, (x + 1) * TILE, y * TILE])
            elif char == "\\":
                segments.append([x * TILE, y * TILE, (x + 1) * TILE, (y + 1) * TILE])
            if y > 0 and not _solid(rows, x, y - 1) and not low_side:
                horizontal.append((y, x))
            if y < H - 1 and not _solid(rows, x, y + 1):
                horizontal.append((y + 1, x))
            if x > 0 and not _solid(rows, x - 1, y) and low_side != -1:
                vertical.append((x, y))
            if x < W - 1 and not _solid(rows, x + 1, y) and low_side != 1:
                vertical.append((x + 1, y))
    for y, start, end in _merge(horizontal):
        segments.append([start * TILE, y * TILE, end * TILE, y * TILE])
    for x, start, end in _merge(vertical):
        segments.append([x * TILE, start * TILE, x * TILE, end * TILE])

    right, bottom = W * TILE, H * TILE
    segments += [[0, 0, right, 0], [0, 0, 0, bottom], [right, 0, right, bottom]]
    if open_floor is None:
        segments.append([0, bottom, right, bottom])
    else:
        segments.append([0, bottom, open_floor[0] * TILE, bottom])
        segments.append([(open_floor[1] + 1) * TILE, bottom, right, bottom])
    return segments


def tiles(rows, sheet_index):
    """Midground tiles, as [cell x, cell y, sheet, tile x, tile y]: an edge
    or corner piece where rock meets air, and the fill tile inside."""
    result = []
    for y in range(H):
        for x in range(W):
            char = rows[y][x]
            if char == ".":
                continue
            if char in SLOPE_TILES:
                tx, ty = SLOPE_TILES[char]
            else:
                up, down = not _solid(rows, x, y - 1), not _solid(rows, x, y + 1)
                left, right = not _solid(rows, x - 1, y), not _solid(rows, x + 1, y)
                ty = 1 if up else 3 if down else 2
                tx = 1 if left and not right else 3 if right and not left else 2
            result.append([x, y, sheet_index, tx, ty])
    return result


def background(sheet_index):
    return [[x, y, sheet_index, FILL_TILE[0], FILL_TILE[1]] for y in range(H) for x in range(W)]
