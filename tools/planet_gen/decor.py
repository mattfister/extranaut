"""Dresses a finished room. Nothing here changes where the player can go:
decorations are tiles and animated sprites with no collision, drawn in the
room's empty cells, on its floors' top edges or in its background.

Each zone has its own decorations, in the spirit of Zorta's: grass in the
warrens, windows onto space in gravitor, ruins in pyrite, giant mushrooms in
emerald and machinery in boiling point. The dome in the rock sheets is not
used: it is the ship the player arrived in, not scenery.
"""
from . import render
from .reach import W, H
from .room import UNKILLABLE, TILE
from .sheets import has_tiles

## Zorta's starfield: four tiles of the rockBg sheet.
SPACE_SHEET = "rockBg"
SPACE_TILES = ((5, 1), (6, 1), (5, 2), (6, 2))
## The rock tiles with a straight underside and a straight top.
FLAT_CEILING = (2, 3)
FLAT_FLOOR = (2, 1)
## Grass along the top of a floor: left end, middle, right end. The row
## above holds the tufts that stand up in front of the player's feet.
GRASS_FOR = {(1, 1): (5, 1), (2, 1): (6, 1), (3, 1): (7, 1)}
MUSHROOM_CAP = ((5, 3), (6, 3), (7, 3))
MUSHROOM_STEM = (6, 4)
MUSHROOM_FOOT = (6, 5)
MACHINES = ((5, 4), (6, 4))
MACHINE_ORB = (6, 3)
RUINS_SHEET = "ruins"
RUIN_BLOCKS = ((1, 3), (2, 3), (3, 3))
RUIN_RING = (((2, 1), (3, 1)), ((2, 2), (3, 2)))

## Animated sheets in assets/animations, as (sheet, row).
TWINKLE = ("animations", 0)
SMALL_MUSHROOM = ("animations", 1)
BLADE = ("grass", 0)
WATER = ("waterfall", 0)
TABLET = (("ruinsAnimated", 0), ("ruinsAnimated", 1))

## How likely each decoration is in a room of each zone, and how many.
ZONE_DECOR = {
    "warrens": {
        "grass": 0.7, "small_mushrooms": 0.5, "waterfalls": (0.15, 1, 1),
    },
    "gravitor": {
        "space": (1.0, 2, 4),
    },
    "pyrite": {
        "ruins": (0.65, 2, 5),
    },
    "emerald": {
        "grass": 0.8, "mushrooms": (0.8, 2, 6), "small_mushrooms": 0.6, "waterfalls": (0.3, 1, 2),
    },
    "boiling point": {
        "machines": (0.6, 2, 6),
    },
}
## Rooms on the planet's surface row look out on the sky, whatever the zone.
SURFACE_SPACE = (0.8, 1, 2)
## A sanctuary is always made welcoming.
SANCTUARY_DECOR = {"grass": 1.0, "small_mushrooms": 1.0, "space": (1.0, 1, 2)}
## Water only suits the zones that already have it; tinted orange or red it
## reads as something else.
SANCTUARY_WATERFALLS = (1.0, 1, 2)


class Decor:
    """A room's three tile layers, as {cell: [sheet index, tile x, tile y]},
    and its animated sprites."""

    def __init__(self, rows, sheets, midground, background):
        self.rows = rows
        self.sheets = sheets
        self.background = {
            (x, y): [sheets.index(background), render.FILL_TILE[0], render.FILL_TILE[1]]
            for y in range(H) for x in range(W)
        }
        self.midground = {(t[0], t[1]): t[2:] for t in render.tiles(rows, sheets.index(midground))}
        self.foreground = {}
        self.animated = []
        ## Empty cells already holding a decoration or something to keep clear of.
        self.taken = set()

    def empty(self, cell):
        x, y = cell
        return 0 <= x < W and 0 <= y < H and self.rows[y][x] == "."

    def free(self, cells):
        return all(self.empty(c) and c not in self.taken for c in cells)

    def floors(self):
        """Empty cells standing on flat rock."""
        return [
            (x, y) for y in range(1, H - 1) for x in range(1, W - 1)
            if self.rows[y][x] == "." and self.rows[y + 1][x] == "#"
        ]

    def put(self, cell, sheet, tile):
        self.midground[cell] = [self.sheets.index(sheet), tile[0], tile[1]]
        self.taken.add(cell)

    def animate(self, layer, cell, animation):
        self.animated.append({
            "layer": layer,
            "sheet": animation[0],
            "row": animation[1],
            "pos": [cell[0] * TILE, cell[1] * TILE],
        })

    def layers(self):
        def as_list(cells):
            return [[x, y] + cells[(x, y)] for (x, y) in sorted(cells, key=lambda c: (c[1], c[0]))]
        return {
            "background": as_list(self.background),
            "midground": as_list(self.midground),
            "foreground": as_list(self.foreground),
        }


def decorate(rows, monsters, player_start, zone, kind, at, sheets, rng):
    """Returns the Decor for a built room."""
    decor = Decor(rows, sheets, zone["midground"], zone["background"])
    for name, x, y in monsters:
        if name in UNKILLABLE:
            _keep_clear(decor, (int(x) // TILE, int(y) // TILE))
    _keep_clear(decor, (int(player_start[0]) // TILE, int(player_start[1]) // TILE))

    wanted = dict(ZONE_DECOR[zone["name"]])
    if at[1] == 0:
        wanted.setdefault("space", SURFACE_SPACE)
    if kind == "sanctuary":
        wanted.update(SANCTUARY_DECOR)
        if "waterfalls" in ZONE_DECOR[zone["name"]]:
            wanted["waterfalls"] = SANCTUARY_WATERFALLS

    sheet = zone["midground"]
    # Background first, then things that stand on floors, largest first, so
    # the big pieces get the space they need.
    if _roll(rng, wanted.get("space")):
        _space(decor, rng, zone["background"], _count(rng, wanted["space"]))
    if _roll(rng, wanted.get("waterfalls")):
        _columns(decor, rng, WATER, _count(rng, wanted["waterfalls"]), 1)
    if _roll(rng, wanted.get("mushrooms")) and has_tiles(sheet, MUSHROOM_CAP + (MUSHROOM_STEM, MUSHROOM_FOOT)):
        _mushrooms(decor, rng, sheet, _count(rng, wanted["mushrooms"]))
    if _roll(rng, wanted.get("ruins")):
        _ruins(decor, rng, _count(rng, wanted["ruins"]))
    if _roll(rng, wanted.get("machines")) and has_tiles(sheet, MACHINES + (MACHINE_ORB,)):
        _machines(decor, rng, sheet, _count(rng, wanted["machines"]))
    if rng.random() < wanted.get("grass", 0.0) and has_tiles(sheet, tuple(GRASS_FOR.values())):
        _grass(decor, rng, sheet)
    if rng.random() < wanted.get("small_mushrooms", 0.0):
        _scatter(decor, rng, SMALL_MUSHROOM, 0.07)
    return decor


def _roll(rng, setting):
    return setting is not None and rng.random() < setting[0]


def _count(rng, setting):
    return rng.randint(setting[1], setting[2])


def _keep_clear(decor, cell):
    for dx in (-1, 0, 1):
        for dy in (-1, 0):
            decor.taken.add((cell[0] + dx, cell[1] + dy))


def _space(decor, rng, background, blobs):
    """Cuts windows in the background that show the stars, edged with the
    background rock's own border tiles."""
    space = set()
    for _ in range(blobs):
        cx, cy = rng.randint(3, W - 4), rng.randint(3, H - 4)
        rx, ry = rng.randint(3, 7), rng.randint(2, 5)
        space.update(
            (x, y) for x in range(cx - rx, cx + rx + 1) for y in range(cy - ry, cy + ry + 1)
            if 0 <= x < W and 0 <= y < H
            and ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1.0
        )
    star = decor.sheets.index(SPACE_SHEET)
    rock = decor.sheets.index(background)
    for x in range(W):
        for y in range(H):
            if (x, y) in space:
                tile = SPACE_TILES[(x % 2) + 2 * (y % 2)]
                decor.background[(x, y)] = [star, tile[0], tile[1]]
                if rng.random() < 0.06:
                    decor.animate("background", (x, y), TWINKLE)
            else:
                tx, ty = render.edge_tile(
                    (x, y - 1) in space, (x, y + 1) in space, (x - 1, y) in space, (x + 1, y) in space
                )
                decor.background[(x, y)] = [rock, tx, ty]


def _columns(decor, rng, animation, count, width):
    """Animated columns behind the room, each from a ceiling down to a
    floor: waterfalls. A column only starts under a
    flat stretch of ceiling and ends on a flat stretch of floor; against a
    corner or a slope its square end shows as an ugly edge."""
    runs = []
    for x in range(2, W - 2 - (width - 1)):
        y = 1
        while y < H - 1:
            if decor.empty((x, y)) and not decor.empty((x, y - 1)):
                end = y
                while end < H - 1 and all(decor.empty((x + i, end)) for i in range(width)):
                    end += 1
                # Flat for a cell either side as well, so the column never
                # ends beside a step or a slope.
                flat = all(
                    _edge(decor, (x + i, y - 1)) == FLAT_CEILING and _edge(decor, (x + i, end)) == FLAT_FLOOR
                    for i in range(width)
                ) and all(
                    (_edge(decor, (side, y - 1)) or (0, 0))[1] == FLAT_CEILING[1]
                    and (_edge(decor, (side, end)) or (0, 0))[1] == FLAT_FLOOR[1]
                    for side in (x - 1, x + width)
                )
                if end - y >= 4 and flat:
                    runs.append((x, y, end))
                y = max(end, y + 1)
            else:
                y += 1
    rng.shuffle(runs)
    used = set()
    for x, top, bottom in runs:
        if count <= 0:
            break
        if any(abs(x - other) < 4 for other in used):
            continue
        used.add(x)
        count -= 1
        for y in range(top, bottom):
            for i in range(width):
                decor.animate("background", (x + i, y), animation)


def _edge(decor, cell):
    """The rock tile drawn in a cell, or None where there is no rock."""
    tile = decor.midground.get(cell)
    return None if tile is None or not (0 <= cell[1] < H) or decor.rows[cell[1]][cell[0]] != "#" else tuple(tile[1:])


def _mushrooms(decor, rng, sheet, count):
    floors = decor.floors()
    rng.shuffle(floors)
    for x, y in floors:
        if count <= 0:
            break
        height = rng.randint(3, 8)
        stem = [(x, y - k) for k in range(height)]
        cap = [(x - 1, y - height), (x, y - height), (x + 1, y - height)]
        # A cell of clear air either side of the stem, so mushrooms do not crowd.
        beside = [(x - 1, y), (x + 1, y)]
        if not decor.free(stem + cap) or any(c in decor.taken for c in beside):
            continue
        decor.put(stem[0], sheet, MUSHROOM_FOOT)
        for cell in stem[1:]:
            decor.put(cell, sheet, MUSHROOM_STEM)
        for cell, tile in zip(cap, MUSHROOM_CAP):
            decor.put(cell, sheet, tile)
        count -= 1


def _machines(decor, rng, sheet, count):
    floors = decor.floors()
    rng.shuffle(floors)
    for x, y in floors:
        if count <= 0:
            break
        if not decor.free([(x, y)]):
            continue
        decor.put((x, y), sheet, rng.choice(MACHINES))
        if rng.random() < 0.4 and decor.free([(x, y - 1)]):
            decor.put((x, y - 1), sheet, MACHINE_ORB)
        count -= 1


def _ruins(decor, rng, count):
    floors = set(decor.floors())
    starts = sorted(floors)
    rng.shuffle(starts)
    for x, y in starts:
        if count <= 0:
            break
        piece = rng.choice(("tablet", "pillar", "pillar", "ring"))
        if piece == "tablet":
            cells = [(x, y - 1), (x, y)]
            if not decor.free(cells):
                continue
            for cell, animation in zip(cells, TABLET):
                decor.animate("midground", cell, animation)
                decor.taken.add(cell)
        elif piece == "pillar":
            cells = [(x, y - k) for k in range(rng.randint(1, 3))]
            if not decor.free(cells):
                continue
            for cell in cells:
                decor.put(cell, RUINS_SHEET, rng.choice(RUIN_BLOCKS))
        else:
            cells = [(x, y - 1), (x + 1, y - 1), (x, y), (x + 1, y)]
            if (x + 1, y) not in floors or not decor.free(cells):
                continue
            for cell, tile in zip(cells, RUIN_RING[0] + RUIN_RING[1]):
                decor.put(cell, RUINS_SHEET, tile)
        count -= 1


def _grass(decor, rng, sheet):
    """Turfs stretches of floor: grass along the top of the rock, tufts in
    front of it, and the odd swaying blade."""
    index = decor.sheets.index(sheet)
    for y in range(1, H):
        x = 0
        while x < W:
            if not _is_turf(decor, x, y):
                x += 1
                continue
            end = x
            while end < W and _is_turf(decor, end, y):
                end += 1
            if rng.random() < 0.65:
                for gx in range(x, end):
                    tile = GRASS_FOR[tuple(decor.midground[(gx, y)][1:])]
                    decor.midground[(gx, y)] = [index, tile[0], tile[1]]
                    above = (gx, y - 1)
                    if has_tiles(sheet, [(tile[0], 0)]) and above not in decor.taken:
                        decor.foreground[above] = [index, tile[0], 0]
                    if rng.random() < 0.25 and decor.free([above]):
                        decor.animate("midground", above, BLADE)
            x = end


def _is_turf(decor, x, y):
    """A flat rock cell with air above and a plain top-edge tile."""
    return (
        decor.rows[y][x] == "#" and decor.empty((x, y - 1))
        and tuple(decor.midground[(x, y)][1:]) in GRASS_FOR
    )


def _scatter(decor, rng, animation, chance):
    for cell in decor.floors():
        if rng.random() < chance and decor.free([cell]):
            decor.animate("midground", cell, animation)
            decor.taken.add(cell)
