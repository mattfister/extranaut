"""The shape of the planet: which rooms connect, and what goes where."""
import collections

GRID = 10
START = (2, 0)
STEP = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}

## What gives each zone its identity: its look and music, the hostiles that
## live there (name: how likely), and the shape of its caves.
##   side_caves   how many caves branch off the middle of a room
##   cave_rx/ry   half-width and half-height of those caves, in cells
##   platforms    how hard to try to add floating ledges
##   slopes       chance that a step in the floor becomes a ramp
##   hover_blocks hover blocks per ordinary room
##   balls        harmless ball monsters per ordinary room
##   elite_rank   how deep a room must be before a BossBot may appear
ZONES = [
    {
        "name": "warrens",
        "midground": "rocks", "background": "bgRocks",
        "tint": [0.75, 0.6, 1.0], "music": "zortaSurface",
        "roster": {"SpikyBallMonster": 5, "Flyer": 4, "JumpBot": 1},
        "style": {
            "side_caves": (2, 4), "cave_rx": (3, 6), "cave_ry": (2, 4), "platforms": (3, 6),
            "slopes": 0.5, "hover_blocks": (0, 0), "balls": (1, 5), "elite_rank": 0.6,
        },
    },
    {
        "name": "gravitor",
        "midground": "rocksBlue", "background": "rockBg",
        "tint": [0.6, 1.0, 0.85], "music": "gravitorZone",
        "roster": {"FlyBot": 5, "Flyer": 3, "AimerTurret": 1},
        "style": {
            "side_caves": (3, 5), "cave_rx": (5, 8), "cave_ry": (4, 6), "platforms": (1, 2),
            "slopes": 0.1, "hover_blocks": (4, 9), "balls": (0, 0), "elite_rank": 0.6,
        },
    },
    {
        "name": "pyrite",
        "midground": "yellowRocks", "background": "bgYellowRocks",
        "tint": [1.0, 0.6, 0.45], "music": "pyriteZone",
        "roster": {"AimerTurret": 5, "DefenseTurretVertical": 4, "JumpBot": 2},
        "style": {
            "side_caves": (2, 3), "cave_rx": (5, 9), "cave_ry": (1, 1), "platforms": (0, 1),
            "slopes": 0.0, "hover_blocks": (0, 1), "balls": (0, 0), "elite_rank": 0.6,
        },
    },
    {
        "name": "emerald",
        "midground": "greenRocks", "background": "greenRocksDark",
        "tint": [0.6, 0.85, 1.0], "music": "emeraldOrbit",
        "roster": {"JumpBot": 5, "HandBot": 4, "DefenseTurretVertical": 1},
        "style": {
            "side_caves": (2, 3), "cave_rx": (5, 8), "cave_ry": (2, 3), "platforms": (2, 4),
            "slopes": 0.6, "hover_blocks": (0, 0), "balls": (0, 0), "elite_rank": 0.6,
        },
    },
    {
        "name": "boiling point",
        "midground": "grayRocks", "background": "redRocksBg",
        "tint": [1.0, 0.55, 0.6], "music": "boilingPoint",
        "roster": {"FlyBot": 3, "SpikyBallMonster": 3, "HandBot": 2, "AimerTurret": 2},
        "style": {
            "side_caves": (3, 5), "cave_rx": (2, 3), "cave_ry": (4, 7), "platforms": (4, 8),
            "slopes": 0.15, "hover_blocks": (0, 2), "balls": (0, 0), "elite_rank": 0.4,
        },
    },
]
## Set-piece rooms, each built its own way. They are dealt out in this order
## to rooms going deeper into the planet, FEATURE_ROUNDS times over, so the
## list runs easy to hard.
FEATURES = [
    "sanctuary", "honeycomb", "spikes", "shaft", "hoverfield", "gallery", "arena", "den",
]
FEATURE_ROUNDS = 2
## Easiest first; the deepest boss room gets the last.
BOSSES = ["OrbBoss", "HeadBoss", "OctoBoss", "FallenExtranaut"]

EXTRA_LINKS = 26
## How often the maze grows from its newest room rather than a random one.
## Lower values give more branches and dead ends.
NEWEST_BIAS = 0.7
MIN_BEHIND_GATE = 3
MAX_BEHIND_GATE = 12
MIN_BOSS_DEPTH = 5
SAVE_POINTS_MIN = 8
SAVE_POINTS_MAX = 10
SAVE_POINT_REACH = 6
INFESTED_ONE_IN = 8
## Floor rows for side openings and left columns for vertical ones.
SIDE_ROWS = (6, 20)
VERTICAL_COLS = (4, 23)
## Vertical openings of the gate room keep clear of its band of rock.
GATE_LEFT_COLS = (4, 6)
GATE_RIGHT_COLS = (21, 23)


class Unbuildable(Exception):
    """This attempt at a world cannot satisfy the rules; try another."""


class WorldMap:
    def __init__(self):
        self.links = {(x, y): {} for x in range(GRID) for y in range(GRID)}
        self.depth = {}
        self.rank = {}
        self.zone = {}
        self.kind = {}
        self.gate = None
        self.gate_dir = None
        ## Which half of the gate room each of its openings is in: "L" or "R".
        self.gate_sides = {}
        self.final = None
        self.behind_gate = set()
        self.bosses = {}
        self.treasure = {}
        self.save_points = set()
        self._distances = {}


def neighbour(at, direction):
    return (at[0] + STEP[direction][0], at[1] + STEP[direction][1])


def distances_from(world, start):
    """Steps along links from start to every room."""
    if start not in world._distances:
        found = {start: 0}
        queue = collections.deque([start])
        while queue:
            at = queue.popleft()
            for direction in world.links[at]:
                nxt = neighbour(at, direction)
                if nxt not in found:
                    found[nxt] = found[at] + 1
                    queue.append(nxt)
        world._distances[start] = found
    return world._distances[start]


def distance(world, a, b):
    return distances_from(world, a)[b]


def build(rng):
    for _ in range(500):
        try:
            return _attempt(rng)
        except Unbuildable:
            continue
    raise RuntimeError("no world satisfies the rules")


def _attempt(rng):
    world = WorldMap()
    parent = _grow_tree(world, rng)
    _place_gate(world, parent)
    _place_bosses(world, rng)
    _add_extra_links(world, rng)
    _place_openings(world, rng)

    world.depth = dict(distances_from(world, START))
    deepest = max(world.depth.values())
    world.rank = {at: world.depth[at] / deepest for at in world.links}

    _assign_zones(world)
    for at in world.links:
        world.kind[at] = "normal"
    world.kind[START] = "start"
    world.kind[world.gate] = "gate"
    world.kind[world.final] = "final"
    for index, at in enumerate(sorted(world.bosses, key=lambda b: (world.depth[b], b))):
        world.bosses[at] = BOSSES[index]
        world.treasure[at] = "AlienArtifact"
        world.kind[at] = "boss"
    _place_powerups(world, rng)
    _place_save_points(world)
    _place_infestations(world, rng)
    _place_features(world, rng)
    return world


def _in_grid(at):
    return 0 <= at[0] < GRID and 0 <= at[1] < GRID


def _link(world, at, direction):
    world.links[at][direction] = 0
    world.links[neighbour(at, direction)][OPPOSITE[direction]] = 0
    world._distances.clear()


def _grow_tree(world, rng):
    """A spanning tree over the grid. Returns each room's parent."""
    parent = {START: None}
    active = [START]
    while active:
        index = len(active) - 1 if rng.random() < NEWEST_BIAS else rng.randrange(len(active))
        at = active[index]
        options = [d for d in "NESW" if _in_grid(neighbour(at, d)) and neighbour(at, d) not in parent]
        if not options:
            active.pop(index)
            continue
        direction = rng.choice(options)
        nxt = neighbour(at, direction)
        parent[nxt] = at
        _link(world, at, direction)
        active.append(nxt)
    return parent


def _subtree(parent, top):
    children = collections.defaultdict(list)
    for at, above in parent.items():
        children[above].append(at)
    found, todo = set(), [top]
    while todo:
        at = todo.pop()
        found.add(at)
        todo.extend(children[at])
    return found


def _place_gate(world, parent):
    """The final room is the deepest in the bottom row; the gate is the
    nearest room above it that everything beyond must pass through."""
    tree_depth = dict(distances_from(world, START))
    world.final = max((at for at in world.links if at[1] == GRID - 1), key=lambda at: (tree_depth[at], at))
    below = world.final
    at = parent[below]
    while at is not None and at != START:
        behind = _subtree(parent, below)
        if len(behind) > MAX_BEHIND_GATE:
            break
        if len(world.links[at]) == 2 and len(behind) >= MIN_BEHIND_GATE:
            world.gate = at
            world.behind_gate = behind
            world.gate_dir = next(d for d in world.links[at] if neighbour(at, d) == below)
            return
        below, at = at, parent[at]
    raise Unbuildable("no room can hold the artifact door")


def _farthest_first(world, candidates, chosen, count):
    """Adds to chosen, one at a time, the candidate farthest from all of it."""
    chosen = list(chosen)
    picked = []
    candidates = sorted(candidates)
    while len(picked) < count and candidates:
        best = max(candidates, key=lambda at: (min(distance(world, at, c) for c in chosen), at))
        picked.append(best)
        chosen.append(best)
        candidates.remove(best)
    return picked


def _place_bosses(world, rng):
    tree_depth = distances_from(world, START)
    leaves = [
        at for at in world.links
        if len(world.links[at]) == 1
        and at not in world.behind_gate
        and at != START
        and tree_depth[at] >= MIN_BOSS_DEPTH
    ]
    picked = _farthest_first(world, leaves, [START], len(BOSSES))
    if len(picked) < len(BOSSES):
        raise Unbuildable("too few dead ends for the bosses")
    world.bosses = {at: "" for at in picked}


def _add_extra_links(world, rng):
    """Loops, so the map is not one long corridor. Boss rooms stay dead ends
    and nothing bypasses the gate."""
    options = []
    for at in sorted(world.links):
        for direction in "ES":
            other = neighbour(at, direction)
            if not _in_grid(other) or direction in world.links[at]:
                continue
            if world.gate in (at, other) or at in world.bosses or other in world.bosses:
                continue
            if (at in world.behind_gate) != (other in world.behind_gate):
                continue
            options.append((at, direction))
    rng.shuffle(options)
    for at, direction in options[:EXTRA_LINKS]:
        _link(world, at, direction)


def _place_openings(world, rng):
    gate = world.gate
    arrive = next(d for d in world.links[gate] if d != world.gate_dir)
    if arrive == "W" or world.gate_dir == "E":
        near = "L"
    elif arrive == "E" or world.gate_dir == "W":
        near = "R"
    else:
        near = rng.choice("LR")
    world.gate_sides = {arrive: near, world.gate_dir: "R" if near == "L" else "L"}

    for at in sorted(world.links):
        for direction in "ES":
            if direction not in world.links[at]:
                continue
            other = neighbour(at, direction)
            if direction == "E":
                pos = rng.randint(*SIDE_ROWS)
            else:
                cols = VERTICAL_COLS
                for room, facing in ((at, "S"), (other, "N")):
                    if room == gate:
                        cols = GATE_LEFT_COLS if world.gate_sides[facing] == "L" else GATE_RIGHT_COLS
                pos = rng.randint(*cols)
            world.links[at][direction] = pos
            world.links[other][OPPOSITE[direction]] = pos


def _assign_zones(world):
    seeds = [START] + _farthest_first(world, [at for at in world.links if at != START], [START], len(ZONES) - 1)
    queue = collections.deque()
    for index, at in enumerate(seeds):
        world.zone[at] = index
        queue.append(at)
    while queue:
        at = queue.popleft()
        for direction in sorted(world.links[at]):
            nxt = neighbour(at, direction)
            if nxt not in world.zone:
                world.zone[nxt] = world.zone[at]
                queue.append(nxt)


def _spread(rooms, count, rng):
    """count rooms spaced evenly through a list, with a little jitter."""
    picked = []
    span = len(rooms) / count
    for i in range(count):
        low = int(i * span)
        high = max(low, int((i + 1) * span) - 1)
        picked.append(rooms[rng.randint(low, high)])
    return picked


def _plain_rooms(world):
    """Rooms with nothing special in them yet, nearest the start first."""
    return sorted(
        (at for at in world.links
         if world.kind[at] == "normal" and at not in world.treasure
         and at not in world.save_points and at not in world.behind_gate),
        key=lambda at: (world.depth[at], at),
    )


def dead_ends(world):
    """Rooms with one way in that a powerup may be tucked into."""
    return sorted(
        at for at in world.links
        if len(world.links[at]) == 1 and at != START
        and at not in world.bosses and at not in world.behind_gate
    )


def _tuck_away(world, at):
    """The room a powerup picked for room at should go in: an empty dead end
    of the same zone if there is one, the nearest in depth, so a side trip
    is rewarded. Otherwise the room itself."""
    free = [
        end for end in dead_ends(world)
        if end not in world.treasure and world.zone[end] == world.zone[at]
    ]
    if not free:
        return at
    return min(free, key=lambda end: (abs(world.depth[end] - world.depth[at]), end))


def _place_powerups(world, rng):
    rooms = _plain_rooms(world)
    # The nearest few rooms are left alone so the first gun is a walk away.
    for index, at in enumerate(_spread(rooms[3:], 6, rng)):
        at = _tuck_away(world, at)
        world.treasure[at] = "GunPowerup" if index % 2 == 0 else "HpPowerup"
        world.kind[at] = "vault"
    for at in _spread(_plain_rooms(world), 6, rng):
        world.treasure[at] = "FuelPowerup"
    # Fuel is moved afterwards, so a dead end goes to a gun or HP powerup
    # first: those sit in vaults, which suit a room with one way in.
    for at in sorted(a for a, name in world.treasure.items() if name == "FuelPowerup"):
        end = _tuck_away(world, at)
        if end != at:
            del world.treasure[at]
            world.treasure[end] = "FuelPowerup"


def _place_save_points(world):
    world.save_points = {START}
    candidates = [
        at for at in sorted(world.links)
        if world.kind[at] == "normal" and at not in world.treasure
    ]

    def worst():
        return max(min(distance(world, at, s) for s in world.save_points) for at in world.links)

    while len(world.save_points) < SAVE_POINTS_MIN or worst() > SAVE_POINT_REACH:
        if len(world.save_points) >= SAVE_POINTS_MAX:
            raise Unbuildable("save points would be too far apart")
        picked = _farthest_first(world, [c for c in candidates if c not in world.save_points], world.save_points, 1)
        world.save_points.add(picked[0])


def _place_infestations(world, rng):
    rooms = _plain_rooms(world)
    for at in rng.sample(rooms, max(6, len(rooms) // INFESTED_ONE_IN)):
        world.kind[at] = "infested"


def _place_features(world, rng):
    """Turns some ordinary rooms into set pieces, spread through the planet
    with the gentler ones nearer the start."""
    count = len(FEATURES) * FEATURE_ROUNDS
    # The first few rooms stay ordinary, so the opening teaches the basics.
    rooms = sorted(_spread(_plain_rooms(world)[4:], count, rng), key=lambda at: (world.depth[at], at))
    # Each pass through the list covers a deeper band of the planet, so the
    # two rooms of a kind are far apart.
    for index, at in enumerate(rooms):
        world.kind[at] = FEATURES[index % len(FEATURES)]
