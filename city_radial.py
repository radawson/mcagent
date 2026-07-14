#!/usr/bin/env python3
"""
Atlantis city -- RADIAL v2: curved terraces, round towers, tholoi.

WHY RADIAL (Rick's call, and it fixes a real bug):
  v1 placed RECTANGULAR houses on CURVED streets and snapped each to the nearest 90 degrees, so a
  house on a stretch of street running at 40 deg sits visibly skewed against its own road. The skew
  is a symptom of rectangles having an ORIENTATION. A circle does not. Round buildings read correctly
  at EVERY angle on the ring -- so the most faithful design and the fix for the ugliest defect are the
  same move.

  Plato gives us the word: the zones were "turned as with a lathe" (§A). The city's defining verb is
  TURNING. Its architecture should obey that, not fight it.

  And the site is now the cold north ATLANTIC -- whose own building tradition is the ROUNDHOUSE
  (brochs, nuraghi, Iron Age roundhouses). The Greek THOLOS covers the monumental end. It coheres.

FORM:
  * CURVED TERRACES  -- continuous rows of dwellings following each ring road; the facade is an arc,
                        the party walls run radially. Two terraces per band, back to back, each facing
                        its own street, with a service alley between.
  * ROUND TOWERS     -- at ring-road / radial-street crossings. Silhouette + punctuation.
  * THOLOI           -- round, domed; standing in plazas where a terrace unit is left out.

Everything is a radius-and-angle test -- the same maths the ring engine has used since op #1.

Emits ONE angular WEDGE per .schem. Paste with `-a`: the schem holds ONLY solid blocks, so doorways,
windows and interiors (cells we never set) let the existing air show through. Nothing is carved.

DETERMINISM (INVARIANT 1): seeded from (ring, sector, band, unit). Never the clock. A re-run must
reproduce the same city block-for-block or the build stops being idempotent.
"""
import argparse, math, random
from schem import write_schem
from vmodel import VModel

P = dict(
    plinth  = "minecraft:stone_bricks",
    wall    = ["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_quartz"],
    wall2   = ["minecraft:calcite", "minecraft:smooth_quartz"],
    roof    = ["minecraft:terracotta", "minecraft:granite"],
    parapet = "minecraft:polished_granite",
    lintel  = "minecraft:stripped_oak_log[axis=y]",
    glass   = "minecraft:glass",
    road    = ["minecraft:smooth_stone", "minecraft:stone_bricks", "minecraft:andesite"],
    pave    = "minecraft:cobblestone",
    tower   = "minecraft:calcite",
    tower_cap = "minecraft:polished_granite",
    tholos  = "minecraft:smooth_quartz",
    tholos_dome = "minecraft:waxed_cut_copper",     # copper dome -- orichalcum glint in the roofline
    column  = "minecraft:quartz_pillar[axis=y]",
    # --- the market. ALL the colour in the city lives here. The dwellings stay white and disciplined;
    # the bazaar is where the life is: striped awnings, copper wares, produce.
    awning  = ["minecraft:orange_terracotta", "minecraft:red_terracotta",
               "minecraft:yellow_terracotta", "minecraft:brown_terracotta"],
    post    = "minecraft:stripped_oak_log[axis=y]",
    counter = "minecraft:smooth_stone",
    wares   = ["minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]",
               "minecraft:cut_copper", "minecraft:melon"],     # copper wares: Atlantis was famed for metal
)


def _rng(*key):
    h = 0
    for k in key:
        h = (h * 1000003) ^ (hash(k) & 0xFFFFFFFF)
    return random.Random(h & 0x7FFFFFFF)


def build_wedge(S, ring, sectors, sector, sea=-30, seed=1337):
    V = VModel(S, sea=sea)
    cx, cz, y = V.cx, V.cz, V.y_land          # the land-ring surface the city stands on
    m2b = V.m2b

    r_in, r_out = (V.r_w1, V.r_l1) if ring == 1 else (V.r_w2, V.r_l2)
    dock_d, wall_t = m2b(12), m2b(3)
    road_hw = max(2, round(S / 12))
    # CLEARANCES. The old margins were too tight and the city CLOBBERED THE CIRCUIT WALL: the road
    # band ran to r1+road_w, which lands on the wall's inner face and repaints a course of it at
    # street level, and the towers (radius 5) on the outermost ring road could reach it too.
    # The gap wants to be a FEATURE, not just a setback: real walled cities keep a clear strip inside
    # the ramparts (the Roman POMERIUM) with a road along it for access. So buildings stop well short
    # and a wall-walk street runs inside the wall.
    r0 = r_in + dock_d + 8                     # clear the rock-cut docks
    # THE MARKET QUARTER (Rick's call, and historically exact): markets go where traffic concentrates
    # and where there is open ground -- and the pomerium is BOTH. It is a continuous ring road with
    # dead frontage on one side, and it is the strip every GATE empties into (the canal and the
    # bridges pierce the wall here). Shops built against the inside of a city wall is one of the
    # oldest patterns there is: the souk, the wall-market, the medieval lean-to.
    # It also fixes something else: the city has no COLOUR. White housing is right and disciplined,
    # but bloodless. Colour belongs in the bazaar -- striped awnings, copper wares, produce.
    r_nobuild   = r_out - wall_t - 2            # HARD limit -- nothing may EVER cross this
    r_shops_out = r_out - wall_t - 3            # shop backs, against the rampart
    r_shops_in  = r_shops_out - 7               # shop fronts (open, with counters)
    r_wallroad  = r_shops_in - 4                # the pomerium road itself
    r_stalls    = r_wallroad - 5                # freestanding canopy stalls, city side
    r1          = r_stalls - 3                  # terraced housing stops here
    axis_clear = road_hw + 8                  # clear the cardinal passages/bridges
    canal_clear = 18                          # clear the +X grand canal

    road_w   = max(4, m2b(6))
    band     = max(22, m2b(34))
    unit_arc = max(8, m2b(11))                # a house frontage
    a0 = 2 * math.pi * sector / sectors
    a1 = 2 * math.pi * (sector + 1) / sectors

    rings = []
    rr = r0
    while rr <= r1:
        rings.append(rr)
        rr += band

    B = {}

    def put(dx, dz, yy, blk):
        B[(cx + dx, yy, cz + dz)] = blk

    def blocked(th, r):
        """inside a cardinal passage corridor or the canal?"""
        dx, dz = r * math.cos(th), r * math.sin(th)
        if abs(dz) < axis_clear or abs(dx) < axis_clear:
            return True
        if dx > 0 and abs(dz) < canal_clear:
            return True
        return False

    # ---- terraces: two per band, back to back, each facing its own ring road -----------
    terraces = []                              # (r_front, r_back, faces_in, band_i, terr_i)
    for bi in range(len(rings) - 1):
        ra, rb = rings[bi], rings[bi + 1]
        f_in  = ra + road_w / 2 + 1            # front on the inner street
        f_out = rb - road_w / 2 - 1            # front on the outer street
        depth = (f_out - f_in - 4) / 2         # 4 = service alley
        if depth < 6:
            continue
        terraces.append((f_in, f_in + depth, True, bi, 0))
        terraces.append((f_out, f_out - depth, False, bi, 1))

    # radial streets are laid out FIRST so the terraces know to leave them clear.
    rad_n = max(1, int(round((a1 - a0) * ((r0 + r1) / 2) / max(28, m2b(40)))))
    rad_angles = [a0 + (a1 - a0) * i / rad_n for i in range(rad_n + 1)]

    for (rf, rb_, faces_in, bi, ti) in terraces:
        lo, hi = (min(rf, rb_), max(rf, rb_))
        rmid = (lo + hi) / 2
        n_units = max(1, int(round((a1 - a0) * rmid / unit_arc)))
        for ui in range(n_units):
            ta = a0 + (a1 - a0) * ui / n_units
            tb = a0 + (a1 - a0) * (ui + 1) / n_units
            tc = (ta + tb) / 2
            if blocked(tc, rmid):
                continue
            g = _rng(seed, ring, sector, bi, ti, ui)

            # BUG FIX: terraces used to be laid across the FULL angular span, so they squatted on the
            # radial streets (the road was painted at ground level but the walls above stayed).
            # Keep cross streets CLEAR -- except ~1 in 7, which OVERBUILDS the lane with an archway
            # through it. Real cities do this and it reads far better than a perfect grid.
            street = next((ra for ra in rad_angles if ta <= ra <= tb), None)
            if street is not None and g.random() >= 0.15:
                continue

            kind = g.random()
            if kind < 0.10 and street is None:                     # plaza + tholos
                _tholos(put, y, rmid, tc, m2b, g)
                continue
            h = g.randint(max(4, m2b(5)), max(6, m2b(9)))          # silhouette variation
            # ONE material per house, not per cell. Picking per-cell made every dwelling a random
            # speckle of the same three whites -- which is why the street read as flat.
            mats = (g.choice(P["wall"]), g.choice(P["roof"]))
            _terrace_unit(put, y, lo, hi, ta, tb, tc, h, faces_in, rf, g, m2b,
                          mats, street, road_w)
    # ---- THE MARKET: shops backing the wall + canopy stalls along the pomerium -----------
    shop_arc = max(7, m2b(9))
    n_shops = max(1, int(round((a1 - a0) * r_shops_out / shop_arc)))
    for si in range(n_shops):
        sa = a0 + (a1 - a0) * si / n_shops
        sb = a0 + (a1 - a0) * (si + 1) / n_shops
        sc = (sa + sb) / 2
        if blocked(sc, r_shops_out):
            continue
        g = _rng(seed, "shop", ring, sector, si)
        if g.random() < 0.12:                       # gaps: alleys and stairs up to the wall
            continue
        _shop_unit(put, y, r_shops_in, r_shops_out, sa, sb, g)

    stall_arc = max(9, m2b(12))
    n_stalls = max(1, int(round((a1 - a0) * r_stalls / stall_arc)))
    for si in range(n_stalls):
        sc = a0 + (a1 - a0) * (si + 0.5) / n_stalls
        if blocked(sc, r_stalls):
            continue
        g = _rng(seed, "stall", ring, sector, si)
        if g.random() < 0.45:                       # not shoulder-to-shoulder; leave room to walk
            continue
        _market_stall(put, y, r_stalls, sc, g)

    road_radii = rings + [r_wallroad]              # ring roads + the pomerium market street
    lo_i, hi_i = int(-r_nobuild) - 3, int(r_nobuild) + 4
    for dx in range(lo_i, hi_i):
        for dz in range(lo_i, hi_i):
            r = math.hypot(dx, dz)
            if not (r0 - road_w / 2 <= r <= r_nobuild):     # HARD clamp: never reach the wall
                continue
            th = math.atan2(dz, dx) % (2 * math.pi)
            if not _in_arc(th, a0, a1):
                continue
            on_ring = any(abs(r - rr) <= road_w / 2 for rr in road_radii)
            on_rad = any(abs(_angdiff(th, ra)) * r <= road_w / 2 for ra in rad_angles)
            if on_ring or on_rad:
                put(dx, dz, y, _rng(seed, dx, dz).choice(P["road"]))

    # ---- round towers at the street crossings ------------------------------------------
    for rr in rings:
        for ra in rad_angles:
            if blocked(ra, rr):
                continue
            g = _rng(seed, "tower", ring, sector, int(rr), round(ra, 4))
            trad = max(3, m2b(5))
            if rr + trad + 2 > r1 or rr - trad - 2 < r0:      # keep towers clear of wall AND docks
                continue
            if g.random() < 0.45:
                _tower(put, y, rr, ra, m2b, g)

    return B, V


def _terrace_unit(put, y, lo, hi, ta, tb, tc, h, faces_in, r_front, g, m2b,
                  mats, street, road_w):
    """One dwelling in a curved terrace. Facade is an ARC; party walls run RADIALLY.
    `mats` = (wall, roof) chosen ONCE for the whole house -- per-cell picking made every dwelling a
    speckle of the same three whites, which is what made the street read flat.
    If `street` is not None this unit OVERBUILDS a radial lane: we leave an ARCHWAY through it."""
    wall_mat, roof_mat = mats
    steps = max(6, int((hi - lo)))                       # radial samples
    arc_n = max(6, int((tb - ta) * hi))                  # angular samples (in blocks)
    for i in range(steps + 1):
        r = lo + (hi - lo) * i / steps
        for j in range(arc_n + 1):
            th = ta + (tb - ta) * j / arc_n
            dx, dz = r * math.cos(th), r * math.sin(th)
            dxi, dzi = int(round(dx)), int(round(dz))
            on_face = (i == 0 and faces_in) or (i == steps and not faces_in)
            on_back = (i == steps and faces_in) or (i == 0 and not faces_in)
            on_party = (j == 0 or j == arc_n)
            # inside the lane this house vaults over? then the lower courses stay OPEN (the arch)
            in_arch = street is not None and abs(_angdiff(th, street)) * max(1.0, r) < road_w / 2 + 1
            if not in_arch:
                put(dxi, dzi, y, P["plinth"])                         # floor (road repaints the arch)
            if on_face or on_back or on_party:
                # doorway on the street-facing arc: those cells are simply NEVER PLACED, so the air
                # already there shows through on a `-a` paste. Nothing is carved.
                is_door = on_face and abs(th - tc) < 1.2 / max(1.0, r)
                for yy in range(y + 1, y + h + 1):
                    if is_door and yy in (y + 1, y + 2):
                        continue
                    if in_arch and yy <= y + 4:                       # archway headroom
                        continue
                    put(dxi, dzi, yy, wall_mat)
                if is_door:
                    put(dxi, dzi, y + 3, P["lintel"])
                elif (on_face or on_back) and (j % 4 == 2) and h >= 5 and not in_arch:
                    put(dxi, dzi, y + 3, P["glass"])                  # windows
            put(dxi, dzi, y + h + 1, roof_mat)                        # roof deck (one material)
            if on_face or on_back or on_party:
                put(dxi, dzi, y + h + 2, P["parapet"])


def _shop_unit(put, y, r_in_, r_out_, ta, tb, g):
    """A shop backing onto the rampart, open-fronted onto the pomerium, with a counter and an awning
    projecting over the street. The oldest urban pattern there is: the lean-to against the city wall."""
    wall_mat = g.choice(P["wall"])
    awn = g.choice(P["awning"])
    h = 5
    steps = max(4, int(r_out_ - r_in_))
    arc_n = max(5, int((tb - ta) * r_out_))
    for i in range(steps + 1):
        r = r_in_ + (r_out_ - r_in_) * i / steps
        for j in range(arc_n + 1):
            th = ta + (tb - ta) * j / arc_n
            dxi = int(round(r * math.cos(th)))
            dzi = int(round(r * math.sin(th)))
            on_back = (i == steps)
            on_party = (j == 0 or j == arc_n)
            on_front = (i == 0)
            put(dxi, dzi, y, P["plinth"])
            if on_back or on_party:
                for yy in range(y + 1, y + h + 1):
                    put(dxi, dzi, yy, wall_mat)
            elif on_front:
                put(dxi, dzi, y + 1, P["counter"])                 # the shop counter
                if j % 3 == 1:
                    put(dxi, dzi, y + 2, g.choice(P["wares"]))     # goods on display
            elif i == 1 and j % 4 == 2:
                put(dxi, dzi, y + 1, g.choice(P["wares"]))         # stock behind the counter
            put(dxi, dzi, y + h + 1, g.choice(P["roof"]))          # roof
    # awning projecting over the street, on posts
    for j in range(arc_n + 1):
        th = ta + (tb - ta) * j / arc_n
        for k in (1, 2):
            r = r_in_ - k
            dxi = int(round(r * math.cos(th)))
            dzi = int(round(r * math.sin(th)))
            put(dxi, dzi, y + h, awn)
            if k == 2 and j in (0, arc_n):
                for yy in range(y + 1, y + h):
                    put(dxi, dzi, yy, P["post"])


def _market_stall(put, y, r, th, g):
    """Freestanding canopy stall on the pomerium. Small enough that axis-alignment reads as the
    cheerful ad-hoc clutter of a real market rather than as a grid error."""
    cxr, czr = r * math.cos(th), r * math.sin(th)
    awn = g.choice(P["awning"])
    hw = 2
    for dx in range(-hw, hw + 1):
        for dz in range(-hw, hw + 1):
            X, Z = int(round(cxr + dx)), int(round(czr + dz))
            put(X, Z, y + 4, awn)                                   # canopy
            if abs(dx) == hw and abs(dz) == hw:                     # corner posts
                for yy in range(y + 1, y + 4):
                    put(X, Z, yy, P["post"])
            elif dz == -hw:                                         # counter along one side
                put(X, Z, y + 1, P["counter"])
                if dx % 2 == 0:
                    put(X, Z, y + 2, g.choice(P["wares"]))
            elif abs(dx) < hw and abs(dz) < hw and g.random() < 0.3:
                put(X, Z, y + 1, g.choice(P["wares"]))              # crates on the ground


def _tower(put, y, r, th, m2b, g):
    """Round tower at a street crossing -- the broch/nuraghe register. No orientation, so no skew."""
    cxr, czr = r * math.cos(th), r * math.sin(th)
    rad = max(3, m2b(5))
    h = g.randint(max(9, m2b(14)), max(12, m2b(20)))
    for dx in range(-rad - 1, rad + 2):
        for dz in range(-rad - 1, rad + 2):
            d = math.hypot(dx, dz)
            X, Z = int(round(cxr + dx)), int(round(czr + dz))
            if d <= rad:
                put(X, Z, y, P["plinth"])
            if rad - 1 <= d <= rad:
                for yy in range(y + 1, y + h + 1):
                    put(X, Z, yy, P["tower"])
                if int(round(d * 4 + dx + dz)) % 2 == 0:
                    put(X, Z, y + h + 1, P["tower_cap"])              # crenellations
            elif d < rad - 1:
                put(X, Z, y + h, P["tower_cap"])                       # roof deck


def _tholos(put, y, r, th, m2b, g):
    """Round, domed shrine standing in a plaza. Copper dome -- orichalcum in the roofline."""
    cxr, czr = r * math.cos(th), r * math.sin(th)
    rad = max(4, m2b(6))
    h = max(5, m2b(7))
    for dx in range(-rad - 2, rad + 3):
        for dz in range(-rad - 2, rad + 3):
            d = math.hypot(dx, dz)
            X, Z = int(round(cxr + dx)), int(round(czr + dz))
            if d <= rad + 2:
                put(X, Z, y, P["pave"])                                # plaza paving
            if rad - 1 <= d <= rad:                                    # peristyle columns
                if int(round(math.degrees(math.atan2(dz, dx)))) % 30 < 8:
                    for yy in range(y + 1, y + h + 1):
                        put(X, Z, yy, P["column"])
            if d < rad - 1:
                put(X, Z, y, P["tholos"])
    for k in range(rad):                                               # stepped dome
        rr = rad - 1 - k
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if math.hypot(dx, dz) <= rr:
                    put(int(round(cxr + dx)), int(round(czr + dz)), y + h + 1 + k, P["tholos_dome"])


def _angdiff(a, b):
    d = (a - b) % (2 * math.pi)
    return d - 2 * math.pi if d > math.pi else d


def _in_arc(th, a0, a1):
    a0 %= 2 * math.pi; a1 %= 2 * math.pi
    return (a0 <= th <= a1) if a0 <= a1 else (th >= a0 or th <= a1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=185)
    ap.add_argument("--ring", type=int, choices=(1, 2), default=1)
    ap.add_argument("--sectors", type=int, default=32)
    ap.add_argument("--sector", type=int, default=0)
    ap.add_argument("--sea", type=int, default=-30, help="-30 scratchpad, 63 whirled")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"cityr_r{a.ring}_s{a.sector:02d}.schem"
    B, V = build_wedge(a.scale, a.ring, a.sectors, a.sector, a.sea, a.seed)
    W, H, L, pal, origin = write_schem(B, out)
    print(f"RADIAL city -- ring {a.ring}, sector {a.sector}/{a.sectors} @ S={a.scale}, sea={a.sea}")
    print(f"  curved terraces + round towers + tholoi | ground y={V.y_land}")
    print(f"  {len(B)} blocks | {W}x{H}x{L} | {pal} palette -> {out}")
    print(f"  WEOffset {origin}  ->  //schem load {out[:-6]} ; //paste -o -a")
