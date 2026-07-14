#!/usr/bin/env python3
"""
Atlantis city generator -- the land rings as an actual city.
"The entire area was densely crowded with habitations" (PLATO_SOURCE §E).

METHOD: procedural PLACEMENT, handcrafted GEOMETRY.
Procedural generation gave us correct mass at 5 km but it cannot give detail -- detail is authored,
not computed. So the buildings here are hand-authored parametric pieces (real walls, doorways,
windows, courtyards, parapets), and a layout pass lays ring roads + radial streets across a land ring
and stamps those pieces into the plots, each oriented to face its street.

Emits ONE angular WEDGE of one land ring as a .schem (the rings are far too big for a single
schematic). Paste wedge by wedge:
    python3 city_gen.py --ring 1 --sectors 32 --sector 0 --out city_r1_s00.schem
    # //world scratchpad ; //schem load city_r1_s00 ; //paste -o -a

PASTE WITH `-a` (ignore air). The schem contains ONLY solid blocks -- doorways, windows and interiors
are simply cells we never set, so the air already above the grass shows through. Nothing is carved.

DETERMINISM (INVARIANT 1): the layout is seeded from (ring, sector), never from the clock. A re-run
must reproduce the SAME city block-for-block, or the build stops being idempotent and a restart
mid-run would corrupt it.
"""
import argparse, math, random
from schem import write_schem

STADE_M = 185.0
BUILD_FLOOR = -60
CX, CZ = -10000, 10000

P = dict(
    plinth = "minecraft:stone_bricks",
    wall   = ["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_quartz"],
    roof   = ["minecraft:terracotta", "minecraft:granite"],
    parapet= "minecraft:polished_granite",
    trim   = "minecraft:stripped_oak_log[axis=y]",
    glass  = "minecraft:glass",
    court  = "minecraft:cobblestone",
    road   = ["minecraft:smooth_stone", "minecraft:stone_bricks", "minecraft:andesite"],
    shrine = "minecraft:smooth_quartz",
    shrine_roof = "minecraft:polished_diorite",
)


# ---------------------------------------------------------------- buildings (authored, parametric)
def _shell(c, w, d, h, wallpick, rng, door_x=None, windows=True):
    """plinth + perimeter walls + flat roof + parapet. Cells we skip stay AIR (doorways/windows)."""
    for x in range(w):
        for z in range(d):
            c[(x, 0, z)] = P["plinth"]
    for y in range(1, h + 1):
        for x in range(w):
            for z in range(d):
                if x in (0, w - 1) or z in (0, d - 1):
                    c[(x, y, z)] = wallpick(rng)
    # doorway on the front face (z=0), 2 tall -- simply left unset => air
    dx = w // 2 if door_x is None else door_x
    for y in (1, 2):
        c.pop((dx, y, 0), None)
    c[(dx, 3, 0)] = P["trim"]                                   # lintel
    if windows:
        for y in (3,):
            for x in range(2, w - 2, 3):
                c[(x, y, 0)] = P["glass"]
                c[(x, y, d - 1)] = P["glass"]
            for z in range(2, d - 2, 3):
                c[(0, y, z)] = P["glass"]
                c[(w - 1, y, z)] = P["glass"]
    for x in range(w):                                          # roof deck
        for z in range(d):
            c[(x, h + 1, z)] = rng.choice(P["roof"])
    for x in range(w):                                          # parapet
        for z in range(d):
            if x in (0, w - 1) or z in (0, d - 1):
                c[(x, h + 2, z)] = P["parapet"]
    return c


def townhouse(rng):
    return _shell({}, 9, 7, 6, lambda r: r.choice(P["wall"]), rng)


def shop_row(rng):
    c = _shell({}, 7, 5, 4, lambda r: r.choice(P["wall"]), rng, windows=False)
    for x in range(2, 5):                                       # wide shopfront: unset => open
        for y in (1, 2):
            c.pop((x, y, 0), None)
    c[(2, 3, 0)] = P["trim"]; c[(4, 3, 0)] = P["trim"]
    return c


def courtyard_house(rng):
    w = d = 13
    c = _shell({}, w, d, 5, lambda r: r.choice(P["wall"]), rng)
    for x in range(4, 9):                                       # open central court: strip the roof
        for z in range(4, 9):
            c.pop((x, 6, z), None)
            c.pop((x, 7, z), None)
            c[(x, 0, z)] = P["court"]
    for x in range(4, 9):                                       # court walls (inner face)
        for z in range(4, 9):
            if x in (4, 8) or z in (4, 8):
                for y in range(1, 6):
                    c[(x, y, z)] = P["wall"][0]
    return c


def shrine(rng):
    """a neighbourhood temple -- Plato: 'many temples built and dedicated to many gods' (§D)."""
    w, d, h = 9, 11, 7
    c = {}
    for x in range(w):
        for z in range(d):
            c[(x, 0, z)] = P["plinth"]
            c[(x, 1, z)] = P["plinth"]                          # stylobate
    for x in range(1, w - 1):                                   # cella
        for z in range(4, d - 1):
            for y in range(2, h):
                if x in (1, w - 2) or z in (4, d - 2):
                    c[(x, y, z)] = P["shrine"]
    for x in range(1, w - 1, 2):                                # portico columns
        for y in range(2, h):
            c[(x, y, 2)] = P["shrine"]
    for x in range(w):                                          # entablature + roof
        for z in range(d):
            c[(x, h, z)] = P["shrine_roof"]
            c[(x, h + 1, z)] = P["shrine_roof"] if 1 <= x <= w - 2 and 1 <= z <= d - 2 else None
    return {k: v for k, v in c.items() if v}


def tower(rng):
    c = _shell({}, 7, 7, 12, lambda r: r.choice(P["wall"]), rng)
    for x in range(7):                                          # crenellations
        for z in range(7):
            if (x in (0, 6) or z in (0, 6)) and (x + z) % 2 == 0:
                c[(x, 15, z)] = P["parapet"]
    return c


KIT = [(townhouse, 46), (courtyard_house, 24), (shop_row, 18), (shrine, 6), (tower, 6)]


def pick(rng):
    r = rng.uniform(0, sum(w for _, w in KIT))
    for fn, w in KIT:
        r -= w
        if r <= 0:
            return fn
    return KIT[0][0]


# ---------------------------------------------------------------- placement
def rot_xz(dx, dz, rot):
    if rot == 0: return dx, dz
    if rot == 1: return -dz, dx
    if rot == 2: return -dx, -dz
    return dz, -dx


def build_wedge(S, ring, sectors, sector, seed=1337):
    def m2b(m):
        return max(1, round(m * S / STADE_M))

    sea = BUILD_FLOOR + m2b(30)
    y_land = sea + m2b(8)                      # the land-ring surface the city sits on

    r_w1, r_l1 = 3.5 * S, 5.5 * S              # land ring 1
    r_w2, r_l2 = 7.5 * S, 10.5 * S             # land ring 2
    r_in, r_out = (r_w1, r_l1) if ring == 1 else (r_w2, r_l2)

    # keep clear of: the rock-cut docks (inner band), the circuit wall (outer edge),
    # the cardinal passages/roads, and the +X grand canal.
    dock_d, wall_t, road_hw = m2b(12), m2b(3), max(2, round(S / 12))
    r0 = r_in + dock_d + 6
    r1 = r_out - wall_t - 6
    axis_clear = road_hw + 8
    canal_clear = 7 + 10

    road_w   = max(4, m2b(6))
    band     = max(20, m2b(34))                # radial depth of a city block
    arc_step = max(24, m2b(40))                # target arc length between radial streets

    a0 = 2 * math.pi * sector / sectors
    a1 = 2 * math.pi * (sector + 1) / sectors
    rng = random.Random((seed * 7919) ^ (ring * 104729) ^ (sector * 15485863))   # deterministic!

    B = {}
    ring_roads = [r for r in _frange(r0, r1, band)]
    # radial street angles, spaced by arc at mid-radius
    rmid = (r0 + r1) / 2
    n_rad = max(1, int(round((a1 - a0) * rmid / arc_step)))
    rad_angles = [a0 + (a1 - a0) * i / n_rad for i in range(n_rad + 1)]

    # --- streets (painted onto the land surface) ---
    lo, hi = int(-r1) - 2, int(r1) + 3
    for dx in range(lo, hi):
        for dz in range(lo, hi):
            r = math.hypot(dx, dz)
            if not (r0 - road_w <= r <= r1 + road_w):
                continue
            th = math.atan2(dz, dx) % (2 * math.pi)
            if not _in_arc(th, a0, a1):
                continue
            on_ring = any(abs(r - rr) <= road_w / 2 for rr in ring_roads)
            on_rad = any(abs(_angdiff(th, ra)) * r <= road_w / 2 for ra in rad_angles)
            if on_ring or on_rad:
                B[(CX + dx, y_land, CZ + dz)] = rng.choice(P["road"])

    # --- plots: one building per (band, angular slot) ---
    for bi in range(len(ring_roads) - 1):
        ra, rb = ring_roads[bi], ring_roads[bi + 1]
        rc = (ra + rb) / 2
        for ai in range(n_rad):
            th = (rad_angles[ai] + rad_angles[ai + 1]) / 2
            dx, dz = rc * math.cos(th), rc * math.sin(th)
            if abs(dz) < axis_clear and dx > 0 and dx < canal_clear + r1:   # +X canal corridor
                if abs(dz) < canal_clear:
                    continue
            if abs(dz) < axis_clear or abs(dx) < axis_clear:                # cardinal passages
                continue
            cells = pick(rng)(rng)
            rot = int(round(math.degrees(th) / 90.0)) % 4
            w = max(k[0] for k in cells) + 1
            d = max(k[2] for k in cells) + 1
            ox = int(CX + dx) - w // 2
            oz = int(CZ + dz) - d // 2
            for (lx, ly, lz), blk in cells.items():
                rx, rz = rot_xz(lx - w // 2, lz - d // 2, rot)
                B[(ox + w // 2 + rx, y_land + ly, oz + d // 2 + rz)] = blk
    return B, y_land


def _frange(a, b, step):
    x = a
    while x <= b:
        yield x
        x += step


def _angdiff(a, b):
    d = (a - b) % (2 * math.pi)
    return d - 2 * math.pi if d > math.pi else d


def _in_arc(th, a0, a1):
    a0 %= 2 * math.pi; a1 %= 2 * math.pi
    if a0 <= a1:
        return a0 <= th <= a1
    return th >= a0 or th <= a1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=185)
    ap.add_argument("--ring", type=int, choices=(1, 2), default=1)
    ap.add_argument("--sectors", type=int, default=32)
    ap.add_argument("--sector", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"city_r{a.ring}_s{a.sector:02d}.schem"
    B, y_land = build_wedge(a.scale, a.ring, a.sectors, a.sector, a.seed)
    W, H, L, pal, origin = write_schem(B, out)
    print(f"city ring {a.ring}, sector {a.sector}/{a.sectors} @ S={a.scale}")
    print(f"  ground y={y_land} | {len(B)} blocks | {W}x{H}x{L} | {pal} palette -> {out}")
    print(f"  WEOffset {origin}  ->  //schem load {out[:-6]} ; //paste -o -a")
