#!/usr/bin/env python3
"""
Atlantis command-script generator (FAWE //generate engine, TILED -r).

Emits FAWE console commands (no giant files). All annulus fills use world-anchored
`//generate -r` over chunk-aligned tiles -- validated: `-r` is ABSOLUTE WORLD COORDS,
so tiles stitch seamlessly. Canal/walls/markers use //set boxes.

GEOMETRY: literal Critias figures (PLATO_SOURCE §B/§E): island ⌀5; island-out ring widths
W1=1,L1=2,W2=2,L2=3,W3=3 (core ⌀27); great wall 50 stades past core (r=63.5, metropolis ⌀127).

VERTICAL (this pass, PLATO_SPEC §3 / SOURCE §B): parametric on scale -- block height = metres × S/185
off a sea-level datum; build floor pinned to Y=-60 at every S. Relief: water/canal cut to -30 m,
land rings +8 m above sea, citadel a +20 m cliff-sided plateau, walls above that. Solid fills produce
the cliffs and quays.

DEFERRED: racecourse, full temple + colossus (tunnels, bridges, docks now emitted).
--maxr <blocks> caps build radius for a fast smoke test.

PHASE CONTRACT (design -> exec): the command stream contains `#PHASE <name>` marker lines at every
natural boundary (each zone, walls, canal, passages, docks, markers). They are comments, so an
unmodified harness simply ignores them. The harness MAY opt in and run a `save-all` at each marker --
that is how we stage the S=185 core build so no single save-flush carries the whole ~690M-block delta
into one tick. Exec owns what happens at a boundary (save / checkpoint / pause); design owns where the
boundaries are.

SCALE NOTE (corrected):
  * S=185 CORE (--core, out to water ring 3, r=13.5 stades ~ 5 km) is entirely tractable with SOLID
    fills: ~76k chunks (~3 min pregen), ~690M blocks. Land MUST stay solid here -- the trireme
    tunnels, rock-cut docks and quay faces all need solid land at sea level; hollow it and the
    tunnel water drains into the cavity.
  * The BELT is what explodes: at S=185 it is ~433M columns (~23.5 km ⌀, ~1.7M chunks, ~2.5e9 blocks,
    plausibly tens of GB of region files) and is 95% of the build for 20 km of empty plain.
    BEFORE building the belt at S=185, switch belt land to surface+substrate+edge-quay (it has no
    water/tunnels in it, so hollowing beneath is safe there). Do a disk check first.
  * The generator is radial + tiled, so the belt is purely ADDITIVE -- core-first costs nothing later.
"""
import math, argparse

STADE_M = 185.0
BLOCKS_PER_STADE = 30
TILE = 512

PAL = dict(
    water    = "minecraft:water[level=0]",
    found    = "minecraft:tuff,minecraft:cobbled_deepslate,minecraft:deepslate",
    land_body= "minecraft:stone,minecraft:andesite,minecraft:tuff",
    land_top = "minecraft:grass_block",
    isle_body= "minecraft:calcite,minecraft:granite,minecraft:blackstone",
    isle_top = "minecraft:smooth_stone",
    belt_top = "minecraft:grass_block",
    wall_body= "minecraft:calcite,minecraft:granite,minecraft:blackstone",
    orichalcum="minecraft:cut_copper",
    tin      = "minecraft:iron_block",
    brass    = "minecraft:gold_block",
    parapet  = "minecraft:polished_diorite",
    canal    = "minecraft:water[level=0]",
    canal_wall="minecraft:stone_bricks",
    temple_gold="minecraft:gold_block",
)

CFG = dict(
    cx=-10000, cz=10000,
    build_floor=-60,     # pinned to the scratchpad floor (-61 solid) at every scale
    canal_w=7, canal_overshoot=4, wall_t=2, world="scratchpad",
)


def emit(cfg, maxr=None):
    S = BLOCKS_PER_STADE
    cx, cz = cfg["cx"], cfg["cz"]
    yf = cfg["build_floor"]

    # --- parametric vertical model (metres -> blocks off sea level), PLATO_SPEC §3 ---
    def m2b(m):
        return max(1, round(m * S / STADE_M))
    # Plato fixes the depth of exactly ONE thing: the canal, at 100 ft (~30 m). Ring depth is OUR
    # choice -- 10 m is deep water (a trireme draws 1-2 blocks) and cuts the S=185 core from ~690M
    # blocks to ~300M with every feature intact (tunnels/docks/quays all sit AT SEA LEVEL, above the
    # ring floor). yf stays the canal floor; rf is the city's base.
    depth = m2b(30)                 # canal cut below sea (literal, §B)
    sea = yf + depth                # sea-level datum
    rf = sea - m2b(10)              # ring floor = city base (water rings are 10 m deep)
    y_land = sea + m2b(8)           # land-ring surface (banks above the water)
    y_isle = sea + m2b(20)          # citadel plateau (cliff-topped)
    y_wall = sea + m2b(15)          # circuit-wall top
    y_gwall = sea + m2b(20)         # great-wall top
    # y_bridge = sea + m2b(10)      # reserved for the bridge feature

    # --- radii (stades -> blocks), literal Critias figures ---
    r_isl, r_w1, r_l1 = 2.5 * S, 3.5 * S, 5.5 * S
    r_w2, r_l2, r_w3 = 7.5 * S, 10.5 * S, 13.5 * S
    r_belt = 63.5 * S
    R = r_belt

    ZON = [
        (0, r_isl, "island"), (r_isl, r_w1, "water"), (r_w1, r_l1, "land"),
        (r_l1, r_w2, "water"), (r_w2, r_l2, "land"), (r_l2, r_w3, "water"),
        (r_w3, r_belt, "belt"),
    ]

    c = []
    add = c.append
    tx = f"(x+{-cx})" if cx < 0 else (f"(x-{cx})" if cx > 0 else "x")
    tz = f"(z+{-cz})" if cz < 0 else (f"(z-{cz})" if cz > 0 else "z")

    def dist2_range(x0, x1, z0, z1):
        ndx = max(x0 - cx, 0, cx - x1); ndz = max(z0 - cz, 0, cz - z1)
        fdx = max(abs(x0 - cx), abs(x1 - cx)); fdz = max(abs(z0 - cz), abs(z1 - cz))
        return ndx * ndx + ndz * ndz, fdx * fdx + fdz * fdz

    def annulus(rin, rout, y1, y2, pattern):
        if y2 < y1:
            return
        ro = int(round(rout)); ri = int(round(rin))
        ro2, ri2 = ro * ro, ri * ri
        lo_x, hi_x = math.ceil(cx - rout), math.floor(cx + rout)
        lo_z, hi_z = math.ceil(cz - rout), math.floor(cz + rout)
        sx = math.floor(lo_x / TILE) * TILE
        sz = math.floor(lo_z / TILE) * TILE
        x = sx
        while x <= hi_x:
            z = sz
            while z <= hi_z:
                x0, x1 = max(x, lo_x), min(x + TILE - 1, hi_x)
                z0, z1 = max(z, lo_z), min(z + TILE - 1, hi_z)
                z += TILE
                if x0 > x1 or z0 > z1:
                    continue
                near2, far2 = dist2_range(x0, x1, z0, z1)
                if far2 < ri2 or near2 > ro2:
                    continue
                if maxr is not None and near2 > maxr * maxr:
                    continue
                add(f"//pos1 {x0},{y1},{z0}")
                add(f"//pos2 {x1},{y2},{z1}")
                expr = f"{tx}^2+{tz}^2<={ro2}"
                if ri > 0:
                    expr += f"&&{tx}^2+{tz}^2>{ri2}"
                add(f"//generate -r {pattern} {expr}")
            x += TILE

    def setbox(x1, y1, z1, x2, y2, z2, block):
        add(f"//pos1 {int(x1)},{int(y1)},{int(z1)}")
        add(f"//pos2 {int(x2)},{int(y2)},{int(z2)}")
        add(f"//set {block}")

    def wall(r_edge, cap, t, y_top):
        annulus(r_edge - t, r_edge + t, rf + 1, y_top - 1, PAL["wall_body"])
        annulus(r_edge - t, r_edge + t, y_top, y_top, cap)

    add(f"//world {cfg['world']}")
    add(f"# Atlantis @ {S} b/stade | core r={int(r_w3)} | metropolis r={int(R)} | TILE={TILE}")
    add(f"# vertical: canal floor {yf} | ring floor {rf} | sea {sea} | land {y_land} | citadel {y_isle}"
        f" | wall {y_wall} | great {y_gwall}" + (f" | capped maxr={maxr}" if maxr else ""))

    for inner, outer, kind in ZON:
        if maxr is not None and inner > maxr:
            continue
        add(f"#PHASE zone-{kind}-r{int(outer)}")
        if kind == "water":
            annulus(inner, outer, rf, rf, PAL["found"])       # ring floor (10 m below sea)
            annulus(inner, outer, rf + 1, sea, PAL["water"])  # water column to sea level
        else:
            surf = y_isle if kind == "island" else y_land
            body = PAL["isle_body"] if kind == "island" else PAL["land_body"]
            top = PAL["isle_top"] if kind == "island" else (PAL["belt_top"] if kind == "belt" else PAL["land_top"])
            annulus(inner, outer, rf, surf - 1, body)         # solid mass (cliffs/quays for free)
            annulus(inner, outer, surf, surf, top)

    add("#PHASE walls")
    for r_edge, cap, t, top in [
        (r_isl, PAL["orichalcum"], cfg["wall_t"], y_wall),
        (r_l1, PAL["parapet"], cfg["wall_t"], y_wall),
        (r_l2, PAL["tin"], cfg["wall_t"], y_wall),
        (R, PAL["brass"], cfg["wall_t"] * 2, y_gwall),
    ]:
        if maxr is None or r_edge <= maxr:
            wall(r_edge, cap, t, top)

    add("#PHASE canal")
    w = cfg["canal_w"]
    x_start = cx + int(r_isl)
    x_end = cx + int(min(R, maxr) if maxr else R) + int(cfg["canal_overshoot"] * S)
    # A CANAL IS A CUT THROUGH GROUND. The channel is dug to -30 m while the rings only reach -10 m,
    # so in a void world the trench hangs below the city's base with nothing holding its water in.
    # I first "fixed" that with underwater walls running the whole length -- absurd on inspection
    # (Rick, flying it: "why would we want walls underwater in the water rings?"). Walls were the
    # wrong answer. Give the canal GROUND to be cut through: an embankment from the canal floor up
    # to the ring floor, then dig the channel out of it. The earth holds the water; no underwater
    # walls anywhere. (In whirled the real seabed does this for free.)
    bank = w + 8
    setbox(x_start, yf, cz - bank, x_end, rf, cz + bank, PAL["found"])     # embankment mass
    setbox(x_start, yf + 1, cz - w, x_end, sea, cz + w, PAL["canal"])      # channel dug out of it
    # OPEN CUT: where the canal crosses a LAND ring, the land above the waterline was left SOLID --
    # a submerged bore with its roof one block above the water. Carve air from just above the
    # waterline up past the land surface and the circuit walls: an open channel to the sky, and
    # Plato's "gates ... where the sea passed in" (§B). This box ALSO erases the stale above-water
    # quay walls -- removed geometry does not vanish on an idempotent re-run (INVARIANT 3).
    setbox(x_start, sea + 1, cz - w - 1, x_end, y_wall + 1, cz + w + 1, "minecraft:air")
    # Erase the stale UNDERWATER wall stubs where the canal crosses the WATER RINGS: the ring water
    # and the canal water are one body and should simply meet.
    for ri, ro in [(r_isl, r_w1), (r_l1, r_w2), (r_l2, r_w3)]:
        xa, xb = cx + int(ri), cx + int(ro)
        for zz in (cz - w - 1, cz + w + 1):
            setbox(xa, rf + 1, zz, xb, sea, zz, PAL["canal"])
    # Past the outermost water ring the canal runs out into open sea: raise the embankment to sea
    # level so it reads as a harbour mole and the channel does not spill.
    xw3 = cx + int(r_w3)
    setbox(xw3, rf + 1, cz - bank, x_end, sea, cz - w - 1, PAL["found"])
    setbox(xw3, rf + 1, cz + w + 1, x_end, sea, cz + bank, PAL["found"])
    # Quays: ABOVE the waterline, and ONLY where the canal cuts through LAND.
    for ri, ro in [(r_w1, r_l1), (r_w2, r_l2)]:
        xa, xb = cx + int(ri), cx + int(ro)
        for zz in (cz - w - 1, cz + w + 1):
            setbox(xa, sea + 1, zz, xb, y_land, zz, PAL["canal_wall"])

    # --- radial passages: trireme tunnels through land rings + bridges over water rings (§B) ---
    # "leaving room for a single trireme to pass...covered over so as to leave a way underneath".
    # +X is the open grand canal; the other three cardinals carry roofed tunnels + bridged roads.
    if cfg.get("passages", True) and (maxr is None or maxr >= int(r_w3)):
        add("#PHASE passages")
        tun_hw = max(2, cfg["canal_w"] - 1)
        road_hw = max(2, round(S / 12))
        headroom = m2b(6)
        bridge_y = sea + m2b(10)
        water_rings = [(r_isl, r_w1), (r_l1, r_w2), (r_l2, r_w3)]
        land_rings = [(r_w1, r_l1), (r_w2, r_l2)]

        def radbox(dx, dz, r0, r1, hw, y0, y1, block):
            if dx != 0:
                xa, xb = sorted((cx + dx * r0, cx + dx * r1))
                setbox(xa, y0, cz - hw, xb, y1, cz + hw, block)
            else:
                za, zb = sorted((cz + dz * r0, cz + dz * r1))
                setbox(cx - hw, y0, za, cx + hw, y1, zb, block)

        for dx, dz in [(-1, 0), (0, 1), (0, -1)]:
            for ri, ro in land_rings:                                    # tunnel through the land
                # NB: the circuit wall straddles the land ring's OUTER edge (r +/- wall_t), so a carve
                # that stops at `ro` leaves a solid plug of wall between the tunnel mouth and the water
                # ring beyond -- a dead end. Punch through it.
                roe = ro + cfg["wall_t"] + 1
                radbox(dx, dz, ri, roe, tun_hw, rf, rf, PAL["found"])            # channel floor
                radbox(dx, dz, ri, roe, tun_hw, rf + 1, sea, PAL["canal"])       # water to sea level
                radbox(dx, dz, ri, roe, tun_hw, sea + 1, sea + headroom, "minecraft:air")  # ship headroom (land above = roof)
                radbox(dx, dz, ri, ro, road_hw, y_land, y_land, "minecraft:smooth_stone")  # road across the roof
            for ri, ro in water_rings:                                   # bridge over the water
                radbox(dx, dz, ri, ro, road_hw, bridge_y, bridge_y, "minecraft:stone_bricks")

    # --- rock-cut docks: covered moorage galleries in the land-ring inner quay faces (§B) ---
    # "as they quarried, they hollowed out double docks, having roofs formed out of the native rock."
    # v1: inner (unwalled) faces of L1 & L2 -> water slip + covered headroom, land above = roof.
    # (outer faces + under-island docks deferred: they'd undercut the circuit walls; thread later.)
    if cfg.get("docks", True) and (maxr is None or maxr >= int(r_w3)):
        add("#PHASE docks")
        # 44 m: the excavated ship sheds at Zea are ~40 m long (a trireme is just under 37 m), plus a
        # back wall. This carve is the VOID only -- dock_gen.py builds the sheds, slipways, facing,
        # lights and stores INTO it, because a `-a` paste cannot carve.
        dock_depth = m2b(44)
        dock_head = m2b(6)
        for ri in (r_w1, r_w2):                                   # inner edge of L1, L2
            annulus(ri, ri + dock_depth, rf + 1, sea, PAL["canal"])                   # moorage water
            annulus(ri, ri + dock_depth, sea + 1, sea + dock_head, "minecraft:air")   # covered slip

    # Temple of Poseidon: NOT emitted here. It is a handcrafted schematic (temple_gen.py -> .schem,
    # pasted with //paste -o) per TEMPLE_SPEC.md -- "bulk by math, detail by schematic".
    # The old gold-slab placeholder is retired; build the city, then paste the temple on top.

    add("#PHASE markers")
    setbox(cx, yf + 1, cz, cx, y_isle + 8, cz, "minecraft:redstone_block")
    setbox(cx + 1, y_land + 1, cz, cx + 6, y_land + 1, cz, "minecraft:red_concrete")
    setbox(cx, y_land + 1, cz + 1, cx, y_land + 1, cz + 6, "minecraft:blue_concrete")
    return c, ZON, R


def preview(cfg, ZON, R, cols=79):
    w = cfg["canal_w"]
    sym = {"island": "@", "land": "L", "belt": ".", "water": "~"}

    def kind_at(dx, dz):
        rr = math.hypot(dx, dz)
        if rr > R:
            return " "
        k = " "
        for inner, outer, kd in ZON:
            if (inner < rr <= outer) or (inner == 0 and rr <= outer):
                k = sym[kd]
        return k

    step = max(1, int(2 * R / cols))
    rows = []
    for dz in range(int(-R), int(R) + 1, step):
        row = []
        for dx in range(int(-R), int(R) + 1, step):
            ch = kind_at(dx, dz)
            if dx >= 0 and abs(dz) <= w and ch not in " @":
                ch = "="
            if abs(dx) < step and abs(dz) < step:
                ch = "+"
            row.append(ch)
        rows.append("".join(row))
    return "\n".join(rows)


def add_phase_markers(cmds, every):
    """Insert #PHASE markers every `every` heavy ops, so each save flush carries a BOUNDED
    dirty-chunk delta. Zone-granularity markers are far too coarse: measured save cost is
    ~7s baseline + chunks/200, and one zone (water3) is ~30k chunks -> ~157s -> Watchdog kill.
    Bounding the delta to ~3.5k chunks keeps every flush ~25s with the Watchdog fully armed."""
    if not every:
        return cmds
    out, n = [], 0
    for line in cmds:
        if line.startswith("#PHASE"):
            out.append(line); n = 0; continue
        if line.startswith("//pos1") and n >= every:
            out.append("#PHASE flush"); n = 0
        out.append(line)
        if line.startswith("//generate") or line.startswith("//set"):
            n += 1
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=BLOCKS_PER_STADE)
    ap.add_argument("--out", default="atlantis_30.commands")
    ap.add_argument("--maxr", type=int, default=None, help="cap build radius (blocks) for a smoke test")
    ap.add_argument("--core", action="store_true",
                    help="build only the core (out to water ring 3, r=13.5 stades) -- skips the belt + great wall")
    ap.add_argument("--tile", type=int, default=TILE, help="tile size (chunk-aligned); lower it at big scales")
    ap.add_argument("--phase-every", type=int, default=24,
                    help="insert a #PHASE flush marker every N heavy ops (0=off). "
                         "Bounds the dirty-chunk delta per save. With --tile 256 (256 chunks/tile, "
                         "~2 ops per tile), 24 ops ~ 3k chunks ~ 25s flush (model: 7s + chunks/200).")
    a = ap.parse_args()
    BLOCKS_PER_STADE = a.scale
    TILE = a.tile
    maxr = a.maxr if a.maxr is not None else (int(13.5 * a.scale) if a.core else None)
    cmds, ZON, R = emit(CFG, maxr=maxr)
    cmds = add_phase_markers(cmds, a.phase_every)
    with open(a.out, "w") as f:
        f.write("\n".join(cmds) + "\n")
    gen = sum(1 for l in cmds if l.startswith("//generate"))
    st = sum(1 for l in cmds if l.startswith("//set"))
    print(f"scale={a.scale} b/stade | metropolis r={int(R)} | TILE={TILE}"
          + (f" | CORE ONLY (r<={maxr})" if a.core else (f" | capped maxr={maxr}" if maxr else "")))
    print(f"commands: {len(cmds)} lines | {gen} tiled //generate ops | {st} //set ops -> {a.out}\n")
    print("TOP-DOWN DESIGN  (@=island L=land .=belt ~=water ==canal +=centre):\n")
    print(preview(CFG, ZON, R))
