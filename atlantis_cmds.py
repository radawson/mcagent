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

SCALE NOTE: solid land/water fills are fine at S=30 (thin). At S=185 they explode (~1e10+ blocks) ->
BEFORE S=185, land/belt must switch to surface+substrate+edge-quay (not solid to floor). See TODO.
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
    depth = m2b(30)                 # water/canal cut below sea
    sea = yf + depth                # sea-level datum
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
        annulus(r_edge - t, r_edge + t, yf + 1, y_top - 1, PAL["wall_body"])
        annulus(r_edge - t, r_edge + t, y_top, y_top, cap)

    add(f"//world {cfg['world']}")
    add(f"# Atlantis @ {S} b/stade | core r={int(r_w3)} | metropolis r={int(R)} | TILE={TILE}")
    add(f"# vertical: floor {yf} | sea {sea} (depth {depth}) | land {y_land} | citadel {y_isle}"
        f" | wall {y_wall} | great {y_gwall}" + (f" | SMOKE maxr={maxr}" if maxr else ""))

    for inner, outer, kind in ZON:
        if maxr is not None and inner > maxr:
            continue
        add(f"# zone {kind}  r={int(inner)}..{int(outer)}")
        if kind == "water":
            annulus(inner, outer, yf, yf, PAL["found"])       # sea floor
            annulus(inner, outer, yf + 1, sea, PAL["water"])  # water column to sea level
        else:
            surf = y_isle if kind == "island" else y_land
            body = PAL["isle_body"] if kind == "island" else PAL["land_body"]
            top = PAL["isle_top"] if kind == "island" else (PAL["belt_top"] if kind == "belt" else PAL["land_top"])
            annulus(inner, outer, yf, surf - 1, body)         # solid mass (cliffs/quays for free)
            annulus(inner, outer, surf, surf, top)

    add("# circuit walls (orichalcum / tin / brass) + land-1 parapet")
    for r_edge, cap, t, top in [
        (r_isl, PAL["orichalcum"], cfg["wall_t"], y_wall),
        (r_l1, PAL["parapet"], cfg["wall_t"], y_wall),
        (r_l2, PAL["tin"], cfg["wall_t"], y_wall),
        (R, PAL["brass"], cfg["wall_t"] * 2, y_gwall),
    ]:
        if maxr is None or r_edge <= maxr:
            wall(r_edge, cap, t, top)

    add("# grand canal (+X): cut to sea floor, water to sea level, quay walls")
    w = cfg["canal_w"]
    x_start = cx + int(r_isl)
    x_end = cx + int(min(R, maxr) if maxr else R) + int(cfg["canal_overshoot"] * S)
    setbox(x_start, yf, cz - w, x_end, yf, cz + w, PAL["found"])           # canal floor
    setbox(x_start, yf + 1, cz - w, x_end, sea, cz + w, PAL["canal"])      # water to sea level
    setbox(x_start, yf + 1, cz - w - 1, x_end, y_land, cz - w - 1, PAL["canal_wall"])
    setbox(x_start, yf + 1, cz + w + 1, x_end, y_land, cz + w + 1, PAL["canal_wall"])

    # --- radial passages: trireme tunnels through land rings + bridges over water rings (§B) ---
    # "leaving room for a single trireme to pass...covered over so as to leave a way underneath".
    # +X is the open grand canal; the other three cardinals carry roofed tunnels + bridged roads.
    if cfg.get("passages", True) and (maxr is None or maxr >= int(r_w3)):
        add("# radial passages: tunnels (land rings, roofed) + bridges (water rings)")
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
                radbox(dx, dz, ri, ro, tun_hw, yf, yf, PAL["found"])            # channel floor
                radbox(dx, dz, ri, ro, tun_hw, yf + 1, sea, PAL["canal"])       # water to sea level
                radbox(dx, dz, ri, ro, tun_hw, sea + 1, sea + headroom, "minecraft:air")  # ship headroom (land above = roof)
                radbox(dx, dz, ri, ro, road_hw, y_land, y_land, "minecraft:smooth_stone")  # road across the roof
            for ri, ro in water_rings:                                   # bridge over the water
                radbox(dx, dz, ri, ro, road_hw, bridge_y, bridge_y, "minecraft:stone_bricks")

    # --- rock-cut docks: covered moorage galleries in the land-ring inner quay faces (§B) ---
    # "as they quarried, they hollowed out double docks, having roofs formed out of the native rock."
    # v1: inner (unwalled) faces of L1 & L2 -> water slip + covered headroom, land above = roof.
    # (outer faces + under-island docks deferred: they'd undercut the circuit walls; thread later.)
    if cfg.get("docks", True) and (maxr is None or maxr >= int(r_w3)):
        add("# rock-cut docks: covered water galleries under the inner face of each land ring")
        dock_depth = m2b(12)
        dock_head = m2b(6)
        for ri in (r_w1, r_w2):                                   # inner edge of L1, L2
            annulus(ri, ri + dock_depth, yf + 1, sea, PAL["canal"])                   # moorage water
            annulus(ri, ri + dock_depth, sea + 1, sea + dock_head, "minecraft:air")   # covered slip

    # Temple of Poseidon: NOT emitted here. It is a handcrafted schematic (temple_gen.py -> .schem,
    # pasted with //paste -o) per TEMPLE_SPEC.md -- "bulk by math, detail by schematic".
    # The old gold-slab placeholder is retired; build the city, then paste the temple on top.

    add("# markers: full-height centre column (probe-robust), +X red, +Z blue at land surface")
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=BLOCKS_PER_STADE)
    ap.add_argument("--out", default="atlantis_30.commands")
    ap.add_argument("--maxr", type=int, default=None, help="cap build radius (blocks) for a smoke test")
    a = ap.parse_args()
    BLOCKS_PER_STADE = a.scale
    cmds, ZON, R = emit(CFG, maxr=a.maxr)
    with open(a.out, "w") as f:
        f.write("\n".join(cmds) + "\n")
    gen = sum(1 for l in cmds if l.startswith("//generate"))
    st = sum(1 for l in cmds if l.startswith("//set"))
    print(f"scale={a.scale} b/stade | metropolis r={int(R)} | TILE={TILE}"
          + (f" | SMOKE maxr={a.maxr}" if a.maxr else ""))
    print(f"commands: {len(cmds)} lines | {gen} tiled //generate ops | {st} //set ops -> {a.out}\n")
    print("TOP-DOWN DESIGN  (@=island L=land .=belt ~=water ==canal +=centre):\n")
    print(preview(CFG, ZON, R))
