"""Carves one room and fills it with monsters.

A room is a 30x24 grid of cells. It starts as solid rock; openings, gadgets
(a vault or the artifact gate) and caves are cut out of it, ledges are added
until the player model can get everywhere and back, and monsters are placed.
"""
import random

from . import reach
from .reach import W, H
from .worldmap import BOSSES, FEATURES, FINAL_BOSS, GROUND_BOSS, ODDITIES, ZONES

TILE = 32

## What each hostile costs against a room's difficulty budget.
COST = {
    "JumpBot": 1,
    "Flyer": 1,
    "SpikyBallMonster": 2,
    "DefenseTurretVertical": 2,
    "FlyBot": 3,
    "AimerTurret": 3,
    "HandBot": 4,
    "BossBot1": 6,
    "BossBot2": 7,
    "BossBot3": 9,
}
ELITES = ("BossBot1", "BossBot2", "BossBot3")
HOSTILE = set(COST) | set(BOSSES)
## Monster-class entities that shots cannot remove. A MonsterDoor2 counts them.
UNKILLABLE = {
    "MonsterDoor", "MonsterDoor2", "ArtifactDoor", "SavePoint",
    "AlienArtifact", "GunPowerup", "HpPowerup", "FuelPowerup",
}
DOORS = ("MonsterDoor", "MonsterDoor2", "ArtifactDoor")
TREASURES = ("AlienArtifact", "GunPowerup", "HpPowerup", "FuelPowerup")

GROUND = ("JumpBot", "SpikyBallMonster", "DefenseTurretVertical")
CEILING = ("AimerTurret", "Flyer")
AIR = ("FlyBot",) + ELITES
## Most of one kind in a room.
CAPS = {
    "HandBot": 3, "AimerTurret": 5, "DefenseTurretVertical": 4, "FlyBot": 5,
    "JumpBot": 6, "Flyer": 6, "SpikyBallMonster": 6,
}
## Near the start, at most one of each kind costing this much or more.
EARLY_RANK = 0.25
EARLY_DEAR = 3
## Rooms where the player is not sealed in with a door, so things that shots
## cannot clear may be added freely.
OPEN_KINDS = ("normal",) + tuple(FEATURES) + tuple(ODDITIES)
## Rooms built as an arena for a boss.
BOSS_ROOMS = ("boss", "final")

BASE_BUDGET = 12
RANK_BUDGET = 14
BUDGET_JITTER = 3
BEHIND_GATE_BUDGET = 6
## An ordinary room's budget is scaled by one of these, so some are lulls
## and some are a fight.
MOODS = (0.4, 0.7, 1.0, 1.0, 1.4)
## The share of its budget a quiet, strange room spends.
ODDITY_BUDGET = 0.25
## Hostiles keep this many cells (Chebyshev) from where the player arrives.
SAFE_CELLS = 5
## A powerup lying in the open keeps this far from where the player arrives.
LOOSE_FAR_CELLS = 8
MIN_EMPTY = 120
BALLS = (25, 40)
MAX_REPAIRS = 80
## Set pieces.
GALLERY_TURRETS = (6, 8)
SPIKE_SWARM = (10, 14)
FIELD_HOVER_BLOCKS = (12, 18)
ARENA_HAND_BOTS = 3
SANCTUARY_BALLS = (3, 6)
ATTEMPTS = 400
## A threshold's hall, as a box of cells, and the levels of a strata room:
## the top row of each gallery, which is three cells high.
HALL = (3, 3, W - 4, H - 4)
STRATA = (3, 8, 13, 18)

## The gate room's band of rock, and the tunnel through it.
BAND = (12, 17)
VAULT_W, VAULT_H, PORCH = 8, 4, 3
## A boss arena: how high it is, the lengths of the vault beside it (shorter
## than usual to leave the arena room), and its ledges.
ARENA_HEIGHT = 12
ARENA_VAULT_W = 7
ARENA_FLOORS = (18, 21)
## The floor when the way in comes up from below, to clear the opening.
ARENA_FLOOR_OVER_ENTRY = 17
ARENA_SIDE_LEDGE = (4, 4)     # cells above the floor, length
ARENA_CENTRE_LEDGE = (8, 5)
ARENA_BOSS_HEIGHT = 10
ARENA_BOSS_SPACING = 5
## The ground boss's arena is higher and has no ledges, like its room on
## Zorta, and it sits this far from the right wall and above the floor.
GROUND_ARENA_HEIGHT = 15
GROUND_BOSS_INSET = (1, 2)
## Who stands with the final boss.
FINAL_ESCORTS = ("BossBot1", "BossBot1")


class Unbuildable(Exception):
    """This attempt at a room failed; try the next seed."""


class Room:
    def __init__(self, rows, monsters, player_start, hole):
        self.rows = rows
        self.monsters = monsters
        self.player_start = player_start
        ## Left column of the final room's floor opening, or None.
        self.hole = hole


def build(world, at, seed, slopes=True):
    for attempt in range(ATTEMPTS):
        rng = random.Random(seed * 1000 + attempt)
        try:
            room = _attempt(world, at, rng, slopes)
        except Unbuildable:
            continue
        if not check(world, at, room):
            return room
    raise RuntimeError("could not build room %s" % (at,))


# --- geometry ---------------------------------------------------------------


class _Grid:
    def __init__(self):
        self.solid = {(x, y) for x in range(W) for y in range(H)}
        self.keep_solid = set()
        self.keep_clear = set()
        self.no_spawn = set()
        self.slopes = {}

    def carve(self, cells, keep=False, border=False):
        for cell in cells:
            x, y = cell
            if not reach.in_grid(cell) or cell in self.keep_solid:
                continue
            if not border and (x in (0, W - 1) or y in (0, H - 1)):
                continue
            self.solid.discard(cell)
            if keep:
                self.keep_clear.add(cell)

    def protect(self, cells):
        self.keep_solid.update(c for c in cells if reach.in_grid(c))

    def empty_count(self):
        return W * H - len(self.solid)

    def connected(self):
        """Whether the empty cells form one region."""
        empty = [(x, y) for x in range(W) for y in range(H) if (x, y) not in self.solid]
        if not empty:
            return False
        seen, todo = {empty[0]}, [empty[0]]
        while todo:
            x, y = todo.pop()
            for cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if cell not in seen and reach.is_empty(self.solid, cell):
                    seen.add(cell)
                    todo.append(cell)
        return len(seen) == len(empty)

    def rows(self):
        return [
            "".join(self.slopes.get((x, y), "#") if (x, y) in self.solid else "." for x in range(W))
            for y in range(H)
        ]


def _box(x0, y0, x1, y1):
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def _cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _exits(world, at, hole):
    """The openings the player may leave by, as (direction, position)."""
    exits = sorted(world.links[at].items())
    if hole is not None:
        exits.append(("S", hole))
    return exits


def _open_stub(grid, direction, pos):
    """Marks an opening's protected rock and returns (cells to carve, anchor).
    The anchor is where a cave tunnel starts."""
    if direction in "WE":
        x0, x1 = (0, 3) if direction == "W" else (W - 4, W - 1)
        grid.protect(_box(x0, pos, x1, pos))
        return _box(x0, pos - 3, x1, pos - 1), (4 if direction == "W" else W - 5, pos - 2)
    if direction == "N":
        ledge = range(pos + 3, pos + 6) if pos < 14 else range(pos - 3, pos)
        grid.protect((x, 6) for x in ledge)
        return _box(pos, 0, pos + 2, 7) + [(x, y) for x in ledge for y in (3, 4, 5)], (pos + 1, 8)
    return _box(pos, H - 1, pos + 2, H - 1) + _box(max(1, pos - 2), 20, min(W - 2, pos + 4), 22), (pos + 1, 19)


def _vault(grid, mouth_left, bx, by, length):
    """Reserves the rock of a vault whose block starts at (bx, by): a
    dead-end tunnel two cells high, length - 1 cells long, sealed all round
    but for its mouth. Returns (tunnel cells, door centre, treasure cell)."""
    if mouth_left:
        tunnel = _box(bx, by + 1, bx + length - 2, by + 2)
        door = (bx + 2, by + 2)
        treasure = (bx + length - 3, by + 2)
    else:
        tunnel = _box(bx + 1, by + 1, bx + length - 1, by + 2)
        door = (bx + length - 2, by + 2)
        treasure = (bx + 2, by + 2)
    grid.protect(set(_box(bx, by, bx + length - 1, by + VAULT_H - 1)) - set(tunnel))
    grid.no_spawn.update(tunnel)
    return tunnel, door, treasure


def _place_arena(world, at, grid, rng):
    """Reserves a boss arena: one big flat-floored chamber with three ledges,
    and a vault at floor level on the side away from the way in. In a boss
    room the vault holds the artifact. In the final room it holds the way
    out, a hole in its floor. The ground boss can only shoot to its left, so
    it gets a bare arena with the vault and the player on the left and
    itself in the bottom right corner. Returns what the rest of the build
    needs."""
    links = world.links[at]
    final = world.kind[at] == "final"
    grounded = world.bosses.get(at) == GROUND_BOSS
    if final:
        floor = H - 1
    elif "S" in links:
        floor = ARENA_FLOOR_OVER_ENTRY
    else:
        floor = rng.randint(*ARENA_FLOORS)
    if grounded:
        vault_right = False
    elif ("W" in links) != ("E" in links):
        vault_right = "W" in links
    else:
        vault_right = rng.random() < 0.5
    length = VAULT_W if final else ARENA_VAULT_W
    bx = W - 1 - length if vault_right else 1
    tunnel, door, treasure = _vault(grid, vault_right, bx, floor - 3, length)
    left, right = (3, bx - 1) if vault_right else (bx + length, W - 4)
    centre = (left + right) // 2

    hole = None
    if final:
        hole = bx + 4 if vault_right else bx + 1
        cells = _box(hole, H - 1, hole + 2, H - 1)
        grid.keep_solid.difference_update(cells)
        grid.carve(cells, keep=True, border=True)
    grid.carve(tunnel, keep=True)
    height = GROUND_ARENA_HEIGHT if grounded else ARENA_HEIGHT
    grid.carve(_box(left, max(2, floor - height), right, floor - 1))

    ledges = []
    if not grounded:
        up, length = ARENA_SIDE_LEDGE
        ledges = _box(left + 3, floor - up, left + 2 + length, floor - up)
        ledges += _box(right - 2 - length, floor - up, right - 3, floor - up)
        up, length = ARENA_CENTRE_LEDGE
        ledges += _box(centre - length // 2, floor - up, centre + length // 2, floor - up)
    ledges = [c for c in ledges if c not in grid.keep_clear]
    grid.solid.update(ledges)
    grid.protect(ledges)
    return {
        "door": door,
        "treasure": None if final else treasure,
        "hole": hole,
        # Ways in join the ground boss's arena at its left end, which
        # leaves it a whole floor.
        "hub": (left + 2 if grounded else centre, floor - 3),
        "boss": (
            (right - GROUND_BOSS_INSET[0], floor - GROUND_BOSS_INSET[1]) if grounded
            else (centre, floor - ARENA_BOSS_HEIGHT)
        ),
        # The player appears in the corner farthest from the vault, or from
        # the ground boss.
        "start": (left + 1, floor - 1) if vault_right or grounded else (right - 1, floor - 1),
    }


def _place_vault(grid, rng, blocked):
    """Reserves a vault: a dead-end tunnel two cells high with a porch at its
    mouth. Returns (cells to carve, anchor, door centre, treasure cell)."""
    for _ in range(200):
        mouth_left = rng.random() < 0.5
        by = rng.randint(2, H - 2 - VAULT_H)
        bx = rng.randint(1 + PORCH, W - 2 - VAULT_W) if mouth_left else rng.randint(1, W - 2 - VAULT_W - PORCH)
        x0 = bx - PORCH if mouth_left else bx
        x1 = bx + VAULT_W - 1 if mouth_left else bx + VAULT_W - 1 + PORCH
        footprint = _box(x0 - 1, by - 1, x1 + 1, by + VAULT_H)
        if any(c in blocked or c in grid.keep_solid for c in footprint):
            continue
        if mouth_left:
            porch = _box(bx - PORCH, by, bx - 1, by + 2)
            anchor = (bx - 2, by + 1)
        else:
            porch = _box(bx + VAULT_W, by, bx + VAULT_W - 1 + PORCH, by + 2)
            anchor = (bx + VAULT_W + 1, by + 1)
        tunnel, door, treasure = _vault(grid, mouth_left, bx, by, VAULT_W)
        grid.protect((x, by + VAULT_H - 1) for x in range(x0, x1 + 1))
        return tunnel + porch, anchor, door, treasure
    raise Unbuildable("no space for a vault")


def _place_gate(grid, rng):
    """Splits the room with a band of rock pierced by one tunnel. Returns
    (cells to carve, left anchor, right anchor, door centre)."""
    top = rng.randint(6, 15)
    tunnel = _box(BAND[0], top, BAND[1], top + 1)
    grid.protect(set(_box(BAND[0], 0, BAND[1], H - 1)) - set(tunnel))
    grid.protect(_box(BAND[0] - PORCH, top + 2, BAND[1] + PORCH, top + 2))
    grid.no_spawn.update(tunnel)
    porches = _box(BAND[0] - PORCH, top - 1, BAND[0] - 1, top + 1) + _box(BAND[1] + 1, top - 1, BAND[1] + PORCH, top + 1)
    return tunnel + porches, (BAND[0] - 2, top), (BAND[1] + 2, top), (15, top + 1)


def _brush(center):
    return _box(center[0] - 1, center[1] - 1, center[0] + 1, center[1] + 1)


def _ellipse(center, rx, ry):
    cx, cy = center
    return [
        (x, y)
        for x in range(cx - rx, cx + rx + 1)
        for y in range(cy - ry, cy + ry + 1)
        if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1.0
    ]


def _tunnel(grid, rng, start, hub, x_range):
    """A drunkard's walk with a 3x3 brush from start to hub. Returns the path."""
    lo, hi = x_range
    pos = (min(max(start[0], lo), hi), min(max(start[1], 2), H - 3))
    path = [pos]
    for _ in range(400):
        grid.carve(_brush(pos))
        if _cheb(pos, hub) <= 1:
            break
        dx, dy = hub[0] - pos[0], hub[1] - pos[1]
        if rng.random() < 0.7:
            if rng.random() * (abs(dx) + abs(dy)) < abs(dx):
                steps = [((1 if dx > 0 else -1), 0)]
            else:
                steps = [(0, (1 if dy > 0 else -1))]
        else:
            steps = []
        others = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        rng.shuffle(others)
        for sx, sy in steps + others:
            nxt = (pos[0] + sx, pos[1] + sy)
            if lo <= nxt[0] <= hi and 2 <= nxt[1] <= H - 3 and nxt not in grid.keep_solid:
                pos = nxt
                break
        path.append(pos)
    return path


def _add_platforms(grid, rng, amount):
    for _ in range(rng.randint(*amount) * 12):
        length = rng.randint(3, 6)
        x, y = rng.randint(2, W - 3 - length), rng.randint(5, H - 5)
        cells = [(x + i, y) for i in range(length)]
        clear = [(cx, cy + dy) for cx, cy in cells for dy in (-3, -2, -1, 0, 1, 2)]
        clear += [(x - 1, y), (x + length, y)]
        if any(c in grid.solid or c in grid.keep_clear for c in clear):
            continue
        grid.solid.update(cells)
        if not grid.connected():
            grid.solid.difference_update(cells)


def _add_honeycomb(grid, cells):
    """Fills a cave with a staggered lattice of two-cell blocks."""
    for x, y in cells:
        if y % 3 == 0 and (x + (y // 3 % 2) * 2) % 4 in (0, 1):
            if (x, y) not in grid.keep_clear and 2 <= x <= W - 3 and 3 <= y <= H - 4:
                grid.solid.add((x, y))


def _fill(grid, cells):
    """Turns cells to rock, all or none: nothing is built across an opening."""
    if not any(c in grid.keep_clear for c in cells):
        grid.solid.update(cells)


def _carve_hall(grid, rng, links):
    """A threshold: one plain rectangular hall holding a single piece of
    architecture, as unlike a cave as the cells allow."""
    x0, y0, x1, y1 = HALL
    grid.carve(_box(*HALL))
    # A pyramid would bury an opening on its own side of the room, so it
    # is built where it can be, and usually then.
    pyramids = [m for m, side in (("steps", "S"), ("hanging", "N")) if side not in links]
    if pyramids and rng.random() < 0.6:
        motif = rng.choice(pyramids)
    else:
        motif = rng.choice(("teeth", "monolith", "bars"))
    if motif == "teeth":
        # Columns hanging from the ceiling, longest in the middle or at the
        # ends, over stumps on the floor between them.
        columns = list(range(x0 + 1, x1 - 1, 4))
        inward = rng.random() < 0.5
        for index, x in enumerate(columns):
            from_edge = min(index, len(columns) - 1 - index)
            length = 3 + 3 * (from_edge if inward else len(columns) // 2 - 1 - from_edge)
            _fill(grid, _box(x, y0, x + 1, y0 + length - 1))
        for x in columns[:-1]:
            _fill(grid, _box(x + 2, y1 - 1, x + 3, y1))
    elif motif == "monolith":
        # One block hanging in the middle of the hall.
        _fill(grid, _box(x0 + 6, y0 + 6, x1 - 6, y1 - 6))
    elif motif == "bars":
        # Slabs laid like courses of brick.
        for course, y in enumerate(range(y0 + 4, y1 - 3, 4)):
            for x in range(x0 + 1 + 4 * (course % 2), x1 - 4, 8):
                _fill(grid, _box(x, y, x + 4, y))
    else:
        # A stepped pyramid, standing on the floor or hanging from the ceiling.
        for level in range(5):
            left, right = x0 + 2 + 2 * level, x1 - 2 - 2 * level
            if motif == "steps":
                _fill(grid, _box(left, y1 - 2 * level - 1, right, y1 - 2 * level))
            else:
                _fill(grid, _box(left, y0 + 2 * level, right, y0 + 2 * level + 1))


def _carve_strata(grid, rng):
    """Level galleries the width of the room, stacked up it and joined at
    alternating ends."""
    first = rng.randrange(2)
    for index, top in enumerate(STRATA):
        grid.carve(_box(2, top, W - 3, top + 2))
        if index:
            x = 3 if index % 2 == first else W - 6
            grid.carve(_box(x, top - 2, x + 2, top - 1))


def _carve_hollow(grid, rng, centre):
    """A great round cave about a core of rock. Returns a point in the ring
    beneath the core."""
    rx, ry = rng.randint(5, 7), rng.randint(2, 4)
    grid.protect(c for c in _ellipse(centre, rx, ry) if c not in grid.keep_clear)
    grid.carve(_ellipse(centre, rng.randint(11, 12), rng.randint(8, 9)))
    return (centre[0], min(centre[1] + ry + 2, H - 3))


def _mirror(grid):
    """Makes a cave the same on both sides, which no cave is. The openings
    are left out, so none gets a twin that leads nowhere."""
    for x, y in [(x, y) for x in range(W) for y in range(H) if (x, y) not in grid.solid]:
        if (x, y) not in grid.keep_clear:
            grid.carve([(W - 1 - x, y)])


def _add_slopes(grid, rng, chance):
    for x in range(2, W - 2):
        for y in range(2, H - 1):
            cell = (x, y)
            if cell not in grid.solid or cell in grid.keep_solid or (x, y - 1) in grid.solid:
                continue
            if (x, y + 1) not in grid.solid:
                continue
            for side, char in ((-1, "/"), (1, "\\")):
                low, high = (x + side, y), (x - side, y)
                ramp = (
                    low not in grid.solid
                    and high in grid.solid
                    and high not in grid.slopes
                    and (x + side, y + 1) in grid.solid
                    and (x + side, y + 1) not in grid.slopes
                    and (x + side, y - 1) not in grid.solid
                )
                if ramp and rng.random() < chance:
                    grid.slopes[cell] = char
                    break


# --- analysis ---------------------------------------------------------------


def _door_cells(monsters):
    """The four cells a door fills, for every door among the monsters."""
    cells = set()
    for name, x, y in monsters:
        if name in DOORS:
            cx, cy = int(x) // TILE, int(y) // TILE
            cells.update(((cx - 1, cy - 1), (cx, cy - 1), (cx - 1, cy), (cx, cy)))
    return cells


def _cell_of(x, y):
    return (int(x) // TILE, int(y) // TILE)


def _survey(world, at, solid, hole, extra_starts=()):
    """Where the player can stand, and which of those places cannot reach
    each exit. Returns (nav, nodes, {(direction, pos): stuck nodes})."""
    nav = reach.Nav(solid)
    starts = [reach.entry(d, pos) for d, pos in sorted(world.links[at].items())]
    starts += [(cell, 0.0) for cell in extra_starts]
    nodes = nav.spread(starts)
    stuck = {}
    for direction, pos in _exits(world, at, hole):
        missing = nodes - nav.leavers(nodes, direction, pos)
        if missing or not nodes:
            stuck[(direction, pos)] = missing
    return nav, nodes, stuck


def _repair(world, at, grid, rng, hole, extra_starts):
    """Adds ledges until every place the player can stand leads to every
    exit. Returns the final survey."""
    for _ in range(MAX_REPAIRS):
        nav, nodes, stuck = _survey(world, at, grid.solid, hole, extra_starts)
        if not nodes:
            raise Unbuildable("nowhere to stand")
        if not stuck:
            return nav, nodes
        (direction, pos), missing = sorted(stuck.items())[0]
        targets = reach.exit_cells(direction, pos)
        air = {}
        for node in sorted(missing):
            for cell, cost in nav.flight(node).items():
                air[cell] = min(air.get(cell, reach.BUDGET), cost)
        options = [
            cell for cell, cost in air.items()
            if cost >= 5.0
            and cell not in grid.keep_clear
            and 1 <= cell[0] <= W - 2 and 2 <= cell[1] <= H - 2
            and (cell[0], cell[1] - 1) in air
        ]
        if not options:
            raise Unbuildable("nowhere to put a ledge")
        options.sort(key=lambda c: (min(abs(c[0] - t[0]) + abs(c[1] - t[1]) for t in targets), c))
        ledge = options[rng.randrange(min(4, len(options)))]
        cells = [ledge]
        beside = (ledge[0] + rng.choice((-1, 1)), ledge[1])
        if beside in air and beside not in grid.keep_clear and 1 <= beside[0] <= W - 2:
            cells.append(beside)
        grid.solid.update(cells)
        if grid.connected():
            grid.protect(cells)
        else:
            grid.solid.difference_update(cells)
            grid.keep_clear.add(ledge)
    raise Unbuildable("too many repairs")


# --- monsters ---------------------------------------------------------------


def _ground_pos(cell):
    return [cell[0] * TILE + 16, (cell[1] + 1) * TILE - 16]


def _air_pos(cell):
    return [cell[0] * TILE + 16, cell[1] * TILE + 16]


class _Placer:
    def __init__(self, grid, nav, nodes, safe_from, rng):
        self.grid = grid
        self.rng = rng
        self.safe_from = safe_from
        self.used = set()
        self.monsters = []
        self.within = None
        solid = grid.solid
        usable = lambda c: c not in grid.no_spawn
        self.floor = sorted(c for c in nodes if usable(c))
        self.air = sorted(c for c in nav.air(nodes) if usable(c))
        air = set(self.air)
        self.ceiling = [c for c in self.air if (c[0], c[1] - 1) in solid and c not in nodes]
        self.open_air = [
            c for c in self.air
            if all((c[0] + dx, c[1] + dy) in air for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        ]
        self.wide_air = [
            c for c in self.open_air
            if all((c[0] + dx, c[1] + dy) in air for dx in (-2, 0, 2) for dy in (-2, 0, 2))
        ]
        self.big_floor = [
            c for c in self.floor
            if (c[0] + 1, c[1]) in nodes and (c[0], c[1] - 1) in air and (c[0] + 1, c[1] - 1) in air
        ]

    def _pick(self, cells, safe, spread=1):
        options = [
            c for c in cells
            if all(_cheb(c, u) >= spread for u in self.used)
            and (not safe or all(_cheb(c, s) >= SAFE_CELLS for s in self.safe_from))
            and (self.within is None or c in self.within)
        ]
        return self.rng.choice(options) if options else None

    def add(self, name, safe=True, within=None):
        """Places one monster of a kind, in one of the cells of within if
        given. Returns False if there is no room."""
        self.within = within
        if name == "HandBot":
            cell = self._pick(self.big_floor, safe, 2)
            pos = None if cell is None else [(cell[0] + 1) * TILE, (cell[1] + 1) * TILE - 32]
        elif name in GROUND:
            cell = self._pick(self.floor, safe)
            pos = None if cell is None else _ground_pos(cell)
        elif name in CEILING:
            cell = self._pick(self.ceiling, safe)
            pos = None if cell is None else _air_pos(cell)
        elif name in ELITES or name in BOSSES:
            cell = self._pick(self.wide_air, safe, 2)
            pos = None if cell is None else _air_pos(cell)
        elif name == "HoverBlock":
            cell = self._pick(self.wide_air, safe, 3)
            pos = None if cell is None else _air_pos(cell)
        else:
            cell = self._pick(self.open_air if name == "FlyBot" else self.air, safe)
            pos = None if cell is None else _air_pos(cell)
        if cell is None:
            return False
        self.used.add(cell)
        self.monsters.append([name] + pos)
        return True

    def add_at(self, name, pos, cell):
        self.used.add(cell)
        self.monsters.append([name] + list(pos))

    def firm_floor(self):
        """Standable cells on flat rock, for things that must stay put."""
        return [
            c for c in self.floor
            if (c[0], c[1] + 1) not in self.grid.slopes and all(_cheb(c, u) >= 2 for u in self.used)
        ]


def _add_hostiles(placer, rng, budget, rank, zone, elites=True):
    """Spends a difficulty budget on the zone's own hostiles, plus at most
    one elite in a deep enough room."""
    early = rank < EARLY_RANK
    weights = dict(zone["roster"])
    if elites and rank >= zone["style"]["elite_rank"]:
        weights.update({name: 1 for name in ELITES})
    counts = {}
    elite = False
    failures = 0
    while budget > 0 and failures < 30:
        names = [
            n for n in sorted(weights)
            if COST[n] <= budget
            and counts.get(n, 0) < CAPS.get(n, 99)
            and not (early and COST[n] >= EARLY_DEAR and counts.get(n, 0) >= 1)
            and not (n in ELITES and elite)
        ]
        if not names:
            break
        name = rng.choices(names, [weights[n] for n in names])[0]
        if placer.add(name):
            budget -= COST[name]
            counts[name] = counts.get(name, 0) + 1
            elite = elite or name in ELITES
        else:
            failures += 1


def _add_many(placer, name, count, within=None):
    """Places up to count of a kind, preferring the cells of within."""
    for _ in range(count):
        if not (within is not None and placer.add(name, within=within)):
            placer.add(name)


def _attempt(world, at, rng, slopes):
    kind = world.kind[at]
    zone = ZONES[world.zone[at]]
    style = zone["style"]
    # Rooms that are one great cave rather than a warren of small ones.
    cavern = kind in ("arena", "den", "hoverfield", "honeycomb", "hollow")
    # Rooms laid out whole, with no tunnels wandering between their parts.
    built = kind in ("threshold", "strata")
    links = world.links[at]
    grid = _Grid()
    hole = None
    arena = None

    # Reserve protected rock first, then carve, so nothing cuts into a gadget.
    carvings = []
    anchors = {}
    for direction, pos in sorted(links.items()):
        cells, anchor = _open_stub(grid, direction, pos)
        carvings.append(cells)
        anchors[direction] = anchor
    for cells in carvings:
        grid.carve(cells, keep=True, border=True)

    door = None
    treasure_cell = None
    halves = None
    if kind == "gate":
        cells, left, right, door = _place_gate(grid, rng)
        grid.carve(cells, keep=True)
        halves = {"L": (2, BAND[0] - 2), "R": (BAND[1] + 2, W - 3)}
        hubs = {
            "L": (rng.randint(4, 8), rng.randint(8, 15)),
            "R": (rng.randint(21, 25), rng.randint(8, 15)),
        }
        walks = [(left, "L"), (right, "R")] + [(anchors[d], world.gate_sides[d]) for d in sorted(links)]
    elif kind in BOSS_ROOMS:
        arena = _place_arena(world, at, grid, rng)
        door, treasure_cell, hole = arena["door"], arena["treasure"], arena["hole"]
        halves = {"A": (2, W - 3)}
        hubs = {"A": arena["hub"]}
        walks = [(anchors[key], "A") for key in sorted(anchors)]
    else:
        if kind in ("vault", "boss"):
            cells, anchor, door, treasure_cell = _place_vault(grid, rng, grid.keep_clear | grid.keep_solid)
            grid.carve(cells, keep=True)
            anchors["vault"] = anchor
        halves = {"A": (2, W - 3)}
        for _ in range(100):
            hub = (rng.randint(11, 18), rng.randint(9, 13)) if cavern else (rng.randint(9, 20), rng.randint(7, 16))
            if hub not in grid.keep_solid and hub not in grid.keep_clear:
                break
        hubs = {"A": hub}
        walks = [(anchors[key], "A") for key in sorted(anchors)]

    great_cave = []
    hall_top = set()
    for half, hub in sorted(hubs.items()):
        if arena is not None:
            continue
        if kind == "threshold":
            _carve_hall(grid, rng, links)
        elif kind == "strata":
            _carve_strata(grid, rng)
        elif kind == "hollow":
            hubs[half] = _carve_hollow(grid, rng, hub)
        elif cavern:
            great_cave = _ellipse(hub, rng.randint(9, 11), rng.randint(6, 7))
            grid.carve(great_cave)
        elif kind == "gallery":
            # One long straight hall, four cells high, for turrets to line.
            grid.carve(_box(2, hub[1] - 2, W - 3, hub[1] + 1))
            hall_top = set(_box(2, hub[1] - 2, W - 3, hub[1] - 2))
        elif kind == "shaft":
            # A chimney the full height of the room.
            grid.carve(_box(hub[0] - 4, 2, hub[0] + 4, H - 3))
        else:
            grid.carve(_ellipse(hub, rng.randint(3, 5), rng.randint(2, 3)))
    paths = []
    for start, half in walks:
        if not built:
            paths.append(_tunnel(grid, rng, start, hubs[half], halves[half]))
    if not cavern and not built and arena is None and kind != "gallery":
        # Side caves anywhere in the room, each joined to its hub, so the
        # room spreads across the screen instead of hugging its tunnels.
        for _ in range(rng.randint(*style["side_caves"])):
            half = rng.choice(sorted(hubs))
            lo, hi = halves[half]
            center = (rng.randint(lo + 1, hi - 1), rng.randint(4, H - 5))
            if center in grid.keep_solid:
                continue
            paths.append(_tunnel(grid, rng, center, hubs[half], halves[half]))
            grid.carve(_ellipse(center, rng.randint(*style["cave_rx"]), rng.randint(*style["cave_ry"])))
        for _ in range(rng.randint(1, 3)):
            path = rng.choice(paths)
            grid.carve(_ellipse(rng.choice(path), rng.randint(2, 5), rng.randint(2, 3)))
    if kind == "honeycomb":
        _add_honeycomb(grid, great_cave)
    elif kind == "mirror":
        _mirror(grid)
    if not grid.connected():
        raise Unbuildable("caves do not join up")
    if kind == "shaft":
        _add_platforms(grid, rng, (6, 9))
    elif arena is None and not built and kind not in ("hoverfield", "honeycomb", "gallery", "hollow", "mirror"):
        _add_platforms(grid, rng, style["platforms"])

    # Where the player appears: at the start of the game in the start room,
    # and after dying in any room that has become the checkpoint. It is kept
    # out of gadgets, so nobody respawns sealed inside a vault.
    main_hub = arena["start"] if arena is not None else hubs[sorted(hubs)[0]]
    standing = sorted(
        (
            (x, y) for x in range(2, W - 2) for y in range(2, H - 2)
            if reach.standable(grid.solid, (x, y)) and (x, y) not in grid.keep_clear
        ),
        key=lambda c: (_cheb(c, main_hub), c),
    )
    if not standing:
        raise Unbuildable("nowhere to start")
    start_cell = standing[0]
    grid.protect([(start_cell[0], start_cell[1] + 1)])
    extra = [start_cell]
    nav, nodes = _repair(world, at, grid, rng, hole, extra)
    if grid.empty_count() < MIN_EMPTY:
        raise Unbuildable("too cramped")
    if slopes and arena is None and kind != "threshold":
        _add_slopes(grid, rng, style["slopes"])

    safe_from = [reach.entry(d, pos)[0] for d, pos in sorted(links.items())] + [start_cell]
    placer = _Placer(grid, nav, nodes, safe_from, rng)
    rank = world.rank[at]
    budget = BASE_BUDGET + RANK_BUDGET * rank + rng.randint(-BUDGET_JITTER, BUDGET_JITTER)
    if at in world.behind_gate:
        budget += BEHIND_GATE_BUDGET

    player_start = _ground_pos(start_cell)
    placer.used.add(start_cell)
    if door is not None:
        # A vault's door opens with its treasure still inside, so it counts
        # to two. The final room's opens when nothing but the door is left.
        name = {"gate": "ArtifactDoor", "final": "MonsterDoor"}.get(kind, "MonsterDoor2")
        placer.add_at(name, (door[0] * TILE, door[1] * TILE), door)
    if treasure_cell is not None:
        placer.add_at(world.treasure[at], _ground_pos(treasure_cell), treasure_cell)

    if at in world.save_points:
        spots = sorted(placer.firm_floor(), key=lambda c: (_cheb(c, start_cell), c))
        if not spots:
            raise Unbuildable("nowhere for the save point")
        placer.add_at("SavePoint", _ground_pos(spots[0]), spots[0])
    if kind != "start":
        if at in world.treasure and treasure_cell is None:
            spots = placer.firm_floor()
            far = [c for c in spots if all(_cheb(c, s) >= LOOSE_FAR_CELLS for s in safe_from)]
            spots = sorted(far or spots, key=lambda c: (c[1], c))
            if not spots:
                raise Unbuildable("nowhere for the powerup")
            placer.add_at(world.treasure[at], _ground_pos(spots[0]), spots[0])
        if kind in BOSS_ROOMS:
            # The boss alone, or with its own company: an arena is for the
            # fight, not for the zone's rank and file.
            if kind == "final":
                names = (FINAL_ESCORTS[0], FINAL_BOSS, FINAL_ESCORTS[1])
            elif world.bosses[at] == "BossBots":
                names = ELITES
            else:
                names = (world.bosses[at],)
            first = -(len(names) // 2)
            for index, name in enumerate(names):
                cell = (arena["boss"][0] + (first + index) * ARENA_BOSS_SPACING, arena["boss"][1])
                placer.add_at(name, _air_pos(cell), cell)
        elif kind == "infested":
            for _ in range(rng.randint(*BALLS)):
                placer.add("BallMonster", safe=False)
            _add_hostiles(placer, rng, budget / 4.0, rank, zone)
        elif kind == "sanctuary":
            # A breather: nothing here can hurt.
            for _ in range(rng.randint(*SANCTUARY_BALLS)):
                placer.add("BallMonster", safe=False)
        elif kind == "gallery":
            _add_many(placer, "AimerTurret", rng.randint(*GALLERY_TURRETS), hall_top)
        elif kind == "spikes":
            _add_many(placer, "SpikyBallMonster", rng.randint(*SPIKE_SWARM))
        elif kind == "hoverfield":
            _add_many(placer, "HoverBlock", rng.randint(*FIELD_HOVER_BLOCKS))
            _add_many(placer, "FlyBot", 3)
            _add_many(placer, "Flyer", 3)
        elif kind == "arena":
            _add_many(placer, "HandBot", ARENA_HAND_BOTS)
            _add_hostiles(placer, rng, budget / 3.0, rank, zone)
        elif kind == "den":
            _add_many(placer, "BossBot1", 1)
            _add_many(placer, "BossBot2", 1)
            _add_hostiles(placer, rng, budget / 3.0, rank, zone, elites=False)
        elif kind in ODDITIES:
            _add_hostiles(placer, rng, budget * ODDITY_BUDGET, rank, zone, elites=False)
        elif kind == "normal":
            _add_hostiles(placer, rng, budget * rng.choice(MOODS), rank, zone)
        elif kind != "threshold":
            # A threshold is left empty.
            _add_hostiles(placer, rng, budget, rank, zone)
        if kind in OPEN_KINDS and kind not in ("hoverfield", "sanctuary"):
            _add_many(placer, "HoverBlock", rng.randint(*style["hover_blocks"]))
            for _ in range(rng.randint(*style["balls"])):
                placer.add("BallMonster", safe=False)

    return Room(grid.rows(), placer.monsters, player_start, hole)


# --- validation -------------------------------------------------------------


def check(world, at, room):
    """Everything wrong with a built room. An empty list means it is sound."""
    problems = []
    kind = world.kind[at]
    links = world.links[at]
    rows = room.rows
    if len(rows) != H or any(len(r) != W for r in rows):
        return ["wrong size"]
    solid = reach.parse(rows)
    if W * H - len(solid) < MIN_EMPTY:
        problems.append("too cramped")

    for x in range(W):
        for y in range(H):
            if x not in (0, W - 1) and y not in (0, H - 1):
                continue
            allowed = any((x, y) in reach.exit_cells(d, pos) for d, pos in _exits(world, at, room.hole))
            if ((x, y) not in solid) != allowed:
                problems.append("border cell %d,%d" % (x, y))

    if room.player_start is None:
        return problems + ["no player start"]
    extra = [_cell_of(*room.player_start)]
    doors = _door_cells(room.monsters)
    nav, nodes, stuck = _survey(world, at, solid, room.hole, extra)
    for (direction, pos), missing in sorted(stuck.items()):
        problems.append("%d places cannot leave %s" % (len(missing), direction))
    air = nav.air(nodes)

    entries = [reach.entry(d, pos)[0] for d, pos in sorted(links.items())] + extra
    for name, x, y in room.monsters:
        cell = _cell_of(x, y)
        if name in DOORS:
            continue
        if name in HOSTILE:
            if any(_cheb(cell, e) < SAFE_CELLS - 1 for e in entries):
                problems.append("%s too near an entry" % name)
            if cell not in air:
                problems.append("%s is out of reach" % name)
        if name in UNKILLABLE and cell not in nodes:
            problems.append("%s cannot be reached" % name)

    if doors:
        # With the doors shut, the final room's way out does not count as an
        # exit: it is meant to be out of reach until the boss is dead.
        shut_hole = None if kind == "final" else room.hole
        closed_nav, closed_nodes, closed_stuck = _survey(world, at, solid | doors, shut_hole, extra)
        if kind == "final" and closed_nav.leavers(closed_nodes, "S", room.hole):
            problems.append("the way out is open before the boss is dead")
        if kind == "gate":
            far = (world.gate_dir, links[world.gate_dir])
            near = [d for d in links if d != world.gate_dir][0]
            near_nodes = closed_nav.spread([reach.entry(near, links[near])])
            if near_nodes & closed_nav.leavers(near_nodes, *far):
                problems.append("the gate can be bypassed")
        else:
            if extra[0] not in closed_nodes:
                problems.append("the player start is sealed in the vault")
            for (direction, pos), missing in sorted(closed_stuck.items()):
                problems.append("the vault door blocks the way %s" % direction)
            for name, x, y in room.monsters:
                if name in TREASURES and _cell_of(x, y) in closed_nodes:
                    problems.append("the vault is open")
                if name in HOSTILE and _cell_of(x, y) not in closed_nav.air(closed_nodes):
                    problems.append("%s is sealed in the vault" % name)
    return problems
