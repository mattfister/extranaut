"""Carves one room and fills it with monsters.

A room is a 30x24 grid of cells. It starts as solid rock; openings, gadgets
(a vault or the artifact gate) and caves are cut out of it, ledges are added
until the player model can get everywhere and back, and monsters are placed.
"""
import random

from . import reach
from .reach import W, H
from .worldmap import BOSSES

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
    "MonsterDoor2", "ArtifactDoor", "SavePoint",
    "AlienArtifact", "GunPowerup", "HpPowerup", "FuelPowerup",
}
DOORS = ("MonsterDoor2", "ArtifactDoor")
TREASURES = ("AlienArtifact", "GunPowerup", "HpPowerup", "FuelPowerup")

GROUND = ("JumpBot", "SpikyBallMonster", "DefenseTurretVertical")
CEILING = ("AimerTurret", "Flyer")
AIR = ("FlyBot",) + ELITES
## Most of one kind in a room.
CAPS = {"HandBot": 2, "AimerTurret": 4, "DefenseTurretVertical": 3, "FlyBot": 4}
## Kinds allowed near the start, and the most of the dearer ones there.
EARLY_RANK = 0.25
EARLY = ("JumpBot", "Flyer", "SpikyBallMonster", "DefenseTurretVertical", "AimerTurret", "FlyBot")
EARLY_CAPS = {"AimerTurret": 1, "FlyBot": 1}

BASE_BUDGET = 12
RANK_BUDGET = 14
BUDGET_JITTER = 3
BEHIND_GATE_BUDGET = 6
ELITE_RANK = 0.6
## Hostiles keep this many cells (Chebyshev) from where the player arrives.
SAFE_CELLS = 5
FUEL_FAR_CELLS = 8
MIN_EMPTY = 120
SLOPE_CHANCE = 0.35
BALLS = (25, 40)
MAX_HOVER_BLOCKS = 4
MAX_REPAIRS = 80
SIDE_CAVES = (2, 4)
ATTEMPTS = 400

## The gate room's band of rock, and the tunnel through it.
BAND = (12, 17)
VAULT_W, VAULT_H, PORCH = 8, 4, 3


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
            tunnel = _box(bx, by + 1, bx + VAULT_W - 2, by + 2)
            porch = _box(bx - PORCH, by, bx - 1, by + 2)
            door = (bx + 2, by + 2)
            treasure = (bx + 5, by + 2)
            anchor = (bx - 2, by + 1)
        else:
            tunnel = _box(bx + 1, by + 1, bx + VAULT_W - 1, by + 2)
            porch = _box(bx + VAULT_W, by, bx + VAULT_W - 1 + PORCH, by + 2)
            door = (bx + VAULT_W - 2, by + 2)
            treasure = (bx + 2, by + 2)
            anchor = (bx + VAULT_W + 1, by + 1)
        shell = set(_box(bx, by, bx + VAULT_W - 1, by + VAULT_H - 1)) - set(tunnel)
        grid.protect(shell)
        grid.protect((x, by + VAULT_H - 1) for x in range(x0, x1 + 1))
        grid.no_spawn.update(tunnel)
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


def _add_platforms(grid, rng):
    for _ in range(rng.randint(3, 6) * 12):
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


def _add_slopes(grid, rng):
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
                if ramp and rng.random() < SLOPE_CHANCE:
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
        ]
        return self.rng.choice(options) if options else None

    def add(self, name, safe=True):
        """Places one monster of a kind. Returns False if there is no room."""
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


def _add_hostiles(placer, rng, budget, rank):
    early = rank < EARLY_RANK
    counts = {}
    elite = False
    failures = 0
    while budget > 0 and failures < 30:
        names = [
            n for n in sorted(COST)
            if COST[n] <= budget
            and counts.get(n, 0) < CAPS.get(n, 99)
            and not (early and (n not in EARLY or counts.get(n, 0) >= EARLY_CAPS.get(n, 99)))
            and not (n in ELITES and (elite or rank < ELITE_RANK))
        ]
        if not names:
            break
        name = rng.choice(names)
        if placer.add(name):
            budget -= COST[name]
            counts[name] = counts.get(name, 0) + 1
            elite = elite or name in ELITES
        else:
            failures += 1


def _attempt(world, at, rng, slopes):
    kind = world.kind[at]
    links = world.links[at]
    grid = _Grid()
    hole = rng.randint(4, 23) if kind == "final" else None

    # Reserve protected rock first, then carve, so nothing cuts into a gadget.
    carvings = []
    anchors = {}
    for direction, pos in _exits(world, at, hole):
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
    else:
        if kind in ("vault", "boss"):
            cells, anchor, door, treasure_cell = _place_vault(grid, rng, grid.keep_clear | grid.keep_solid)
            grid.carve(cells, keep=True)
            anchors["vault"] = anchor
        halves = {"A": (2, W - 3)}
        for _ in range(100):
            hub = (rng.randint(11, 18), rng.randint(9, 13)) if kind == "boss" else (rng.randint(9, 20), rng.randint(7, 16))
            if hub not in grid.keep_solid and hub not in grid.keep_clear:
                break
        hubs = {"A": hub}
        walks = [(anchors[key], "A") for key in sorted(anchors)]

    for half, hub in sorted(hubs.items()):
        if kind == "boss":
            grid.carve(_ellipse(hub, rng.randint(8, 10), rng.randint(5, 6)))
        else:
            grid.carve(_ellipse(hub, rng.randint(3, 5), rng.randint(2, 3)))
    paths = []
    for start, half in walks:
        paths.append(_tunnel(grid, rng, start, hubs[half], halves[half]))
    if kind != "boss":
        # Side caves anywhere in the room, each joined to its hub, so the
        # room spreads across the screen instead of hugging its tunnels.
        for _ in range(rng.randint(*SIDE_CAVES)):
            half = rng.choice(sorted(hubs))
            lo, hi = halves[half]
            center = (rng.randint(lo + 1, hi - 1), rng.randint(4, H - 5))
            if center in grid.keep_solid:
                continue
            paths.append(_tunnel(grid, rng, center, hubs[half], halves[half]))
            grid.carve(_ellipse(center, rng.randint(3, 6), rng.randint(2, 4)))
        for _ in range(rng.randint(1, 3)):
            path = rng.choice(paths)
            grid.carve(_ellipse(rng.choice(path), rng.randint(2, 5), rng.randint(2, 3)))
    if not grid.connected():
        raise Unbuildable("caves do not join up")
    _add_platforms(grid, rng)

    # Where the player appears: at the start of the game in the start room,
    # and after dying in any room that has become the checkpoint. It is kept
    # out of gadgets, so nobody respawns sealed inside a vault.
    main_hub = hubs[sorted(hubs)[0]]
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
    if slopes:
        _add_slopes(grid, rng)

    safe_from = [reach.entry(d, pos)[0] for d, pos in sorted(links.items())] + [start_cell]
    placer = _Placer(grid, nav, nodes, safe_from, rng)
    rank = world.rank[at]
    budget = BASE_BUDGET + RANK_BUDGET * rank + rng.randint(-BUDGET_JITTER, BUDGET_JITTER)
    if at in world.behind_gate:
        budget += BEHIND_GATE_BUDGET

    player_start = _ground_pos(start_cell)
    placer.used.add(start_cell)
    if door is not None:
        name = "ArtifactDoor" if kind == "gate" else "MonsterDoor2"
        placer.add_at(name, (door[0] * TILE, door[1] * TILE), door)
    if treasure_cell is not None:
        placer.add_at(world.treasure[at], _ground_pos(treasure_cell), treasure_cell)

    if at in world.save_points:
        spots = sorted(placer.firm_floor(), key=lambda c: (_cheb(c, start_cell), c))
        if not spots:
            raise Unbuildable("nowhere for the save point")
        placer.add_at("SavePoint", _ground_pos(spots[0]), spots[0])
    if kind != "start":
        if world.treasure.get(at) == "FuelPowerup":
            spots = placer.firm_floor()
            far = [c for c in spots if all(_cheb(c, s) >= FUEL_FAR_CELLS for s in safe_from)]
            spots = sorted(far or spots, key=lambda c: (c[1], c))
            if not spots:
                raise Unbuildable("nowhere for the fuel")
            placer.add_at("FuelPowerup", _ground_pos(spots[0]), spots[0])
        if kind == "boss":
            if not placer.add(world.bosses[at]):
                raise Unbuildable("no room for the boss")
            _add_hostiles(placer, rng, budget / 2.0, rank)
        elif kind == "infested":
            for _ in range(rng.randint(*BALLS)):
                placer.add("BallMonster", safe=False)
            _add_hostiles(placer, rng, budget / 4.0, rank)
        else:
            _add_hostiles(placer, rng, budget, rank)
            if kind in ("normal", "final"):
                for _ in range(rng.randint(0, MAX_HOVER_BLOCKS)):
                    placer.add("HoverBlock")

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
        closed_nav, closed_nodes, closed_stuck = _survey(world, at, solid | doors, room.hole, extra)
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
