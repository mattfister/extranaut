"""A coarse model of how the player moves through a room's cell grid.

It is deliberately pessimistic: a room this model can cross, the real player
can cross with room to spare.
"""
import heapq

W, H = 30, 24
## Cells of climb allowed per flight. A full base tank lifts about 11.
BUDGET = 8.0
## What must be left on reaching a ceiling opening, to get clear of the hole
## in the room above.
CEILING_RESERVE = 2.0
OPENING = 3

_MOVES = (
    (0, -1, 1.0),
    (-1, 0, 0.5),
    (1, 0, 0.5),
    (0, 1, 0.0),
    (-1, 1, 0.0),
    (1, 1, 0.0),
)


def parse(rows):
    """The set of solid cells in a picture of a room. Slopes count as solid."""
    return {(x, y) for y, row in enumerate(rows) for x, char in enumerate(row) if char != "."}


def in_grid(cell):
    return 0 <= cell[0] < W and 0 <= cell[1] < H


def is_empty(solid, cell):
    return in_grid(cell) and cell not in solid


def standable(solid, cell):
    return is_empty(solid, cell) and (cell[0], cell[1] + 1) in solid


def fly(solid, start, spent=0.0):
    """Cells reachable in one flight from start, as {cell: cheapest cost}.

    Moving up costs 1, sideways 0.5, and down or diagonally down nothing.
    """
    best = {start: spent}
    queue = [(spent, start)]
    while queue:
        cost, (x, y) = heapq.heappop(queue)
        if cost > best[(x, y)]:
            continue
        for dx, dy, step in _MOVES:
            cell = (x + dx, y + dy)
            if not is_empty(solid, cell):
                continue
            if dx and dy and not (is_empty(solid, (x + dx, y)) and is_empty(solid, (x, y + dy))):
                continue
            total = cost + step
            if total <= BUDGET and total < best.get(cell, BUDGET + 1.0):
                best[cell] = total
                heapq.heappush(queue, (total, cell))
    return best


def reachable(solid, starts):
    """Every cell the player can get to from the (cell, spent) pairs in
    starts, as {cell: cheapest cost on arrival}. Landing refills the tank."""
    best = {}
    todo = list(starts)
    while todo:
        start, spent = todo.pop()
        if not is_empty(solid, start) or best.get(start, BUDGET + 1.0) <= spent:
            continue
        for cell, cost in fly(solid, start, spent).items():
            if standable(solid, cell) and best.get(cell, BUDGET + 1.0) > 0.0:
                best[cell] = cost
                todo.append((cell, 0.0))
            elif cost < best.get(cell, BUDGET + 1.0):
                best[cell] = cost
    return best


def exit_cells(direction, pos):
    """The cells of an opening. pos is the floor row for a side opening and
    the left column for a floor or ceiling opening."""
    if direction == "W":
        return [(0, pos - OPENING + i) for i in range(OPENING)]
    if direction == "E":
        return [(W - 1, pos - OPENING + i) for i in range(OPENING)]
    if direction == "N":
        return [(pos + i, 0) for i in range(OPENING)]
    return [(pos + i, H - 1) for i in range(OPENING)]


def entry(direction, pos):
    """The (cell, spent) a player arrives with through an opening."""
    if direction == "W":
        return ((0, pos - 1), 0.0)
    if direction == "E":
        return ((W - 1, pos - 1), 0.0)
    if direction == "N":
        return ((pos + 1, 0), BUDGET)
    return ((pos + 1, H - 2), BUDGET - CEILING_RESERVE)


def can_leave(reach, direction, pos):
    """Whether a reachable() result gets the player out through an opening."""
    limit = BUDGET - CEILING_RESERVE if direction == "N" else BUDGET
    return any(reach.get(cell, BUDGET + 1.0) <= limit for cell in exit_cells(direction, pos))
