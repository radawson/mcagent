#!/usr/bin/env python3
"""
Atlantis command-script generator (FAWE //generate engine).

Why this exists: the schematic engine (proven by the POC) does NOT scale to full
stade (~1e8-1e9 blocks -> unpasteable clipboard / huge file). This generator emits
a list of FAWE CONSOLE COMMANDS instead of a file: //pos1/#//pos2 select an absolute
bbox and //generate fills an annulus via a NORMALISED expression.

Validated 30-scale on the live server: "14105 blocks have been created", true centered
circle, default normalized coords correct on this build (no -r flag needed).

Key robustness choice: WorldEdit's DEFAULT normalised coordinates (region -> unit cube,
x,y,z in [-1,1]). Each zone's selection is a SQUARE centred on the city with half-width
= outer_radius, so `x^2+z^2<=1` is a TRUE circle of that radius, independent of the
-r/-o raw-coord conventions. Canal / walls / markers use //set boxes.

Scale is BLOCKS_PER_STADE. 30 = engine validation; 180 = a real stade (full build).
The harness (run_commands.sh) pipes each line through the `mc` FIFO and waits for
completion after each heavy op. NOTE: //generate reports "N blocks have been created",
//set reports "Operation completed" -- the harness waits on BOTH.
"""
import math, argparse

BLOCKS_PER_STADE = 30

CFG = dict(
    cx=-10000, cz=10000,                  # test origin in scratchpad
    # vertical model on the scratchpad floor (solid at Y=-61, air from Y=-60 up)
    y_floor=-60, y_water_top=-55, y_land=-54, y_island=-53, y_wall_top=-50,
    # Plato proportions (stades): central island diameter 5; then (kind,width) outward
    island_stades=5,
    bands=[("water", 1), ("land", 1), ("water", 2), ("land", 2), ("water", 3), ("city", 3)],
    canal_w=6,           # half-width of the radial grand canal
    canal_overshoot=90,  # how far past the outer ring the symbolic canal runs to sea
    wall_t=2,            # half-thickness of ring retaining walls
    world="scratchpad",
)


def zones(cfg, S):
    """list of (inner_r, outer_r, kind) from centre outward, in blocks."""
    r = cfg["island_stades"] * S / 2.0
    out = [(0.0, r, "island")]
    for kind, w in cfg["bands"]:
        inner = r
        r = r + w * S
        out.append((inner, r, kind))
    return out


def emit(cfg):
    S = BLOCKS_PER_STADE
    cx, cz = cfg["cx"], cfg["cz"]
    yf, ywt, yl = cfg["y_floor"], cfg["y_water_top"], cfg["y_land"]
    yi, yw = cfg["y_island"], cfg["y_wall_top"]
    Z = zones(cfg, S)
    R = Z[-1][1]                                   # outer radius
    c = []
    add = c.append

    def pos(x1, y1, z1, x2, y2, z2):
        add(f"//pos1 {int(x1)},{int(y1)},{int(z1)}")
        add(f"//pos2 {int(x2)},{int(y2)},{int(z2)}")

    def gen_annulus(rout, rin, y1, y2, pattern):
        # square selection, half-width = rout, centred on the city -> normalised circle
        pos(cx - rout, y1, cz - rout, cx + rout, y2, cz + rout)
        if rin <= 0:
            add(f"//generate {pattern} x^2+z^2<=1")
        else:
            ratio2 = (rin / rout) ** 2
            add(f"//generate {pattern} x^2+z^2<=1&&x^2+z^2>{ratio2:.6f}")

    def setbox(x1, y1, z1, x2, y2, z2, block):
        pos(x1, y1, z1, x2, y2, z2)
        add(f"//set {block}")

    add(f"//world {cfg['world']}")
    add(f"# --- Atlantis @ {S} blocks/stade | outer radius {int(R)} | diameter {int(2 * R)} ---")

    # 1) foundation disc (single stone layer under the whole footprint)
    add("# foundation")
    gen_annulus(R, 0, yf, yf, "minecraft:stone")

    # 2) zones: water columns / land fill + grass top
    for inner, outer, kind in Z:
        add(f"# zone {kind}  r={int(inner)}..{int(outer)}")
        if kind == "water":
            gen_annulus(outer, inner, yf + 1, ywt, "minecraft:water[level=0]")
        else:
            surf = yi if kind == "island" else yl
            gen_annulus(outer, inner, yf + 1, surf - 1, "minecraft:dirt")
            gen_annulus(outer, inner, surf, surf, "minecraft:grass_block")

    # 3) retaining walls on land/island outer edges
    add("# ring walls")
    t = cfg["wall_t"]
    for inner, outer, kind in Z:
        if kind in ("land", "island", "city"):
            gen_annulus(outer + t, outer - t, yf + 1, yw, "minecraft:stone_bricks")

    # 4) symbolic grand canal (radial, +X) out to a harbour mouth, + canal walls
    add("# grand canal (+X) + walls")
    w = cfg["canal_w"]
    x_start = cx + int(Z[0][1])
    x_end = cx + int(R) + cfg["canal_overshoot"]
    setbox(x_start, yf + 1, cz - w, x_end, ywt, cz + w, "minecraft:water[level=0]")
    setbox(x_start, yf + 1, cz - w - 1, x_end, yl, cz - w - 1, "minecraft:stone_bricks")
    setbox(x_start, yf + 1, cz + w + 1, x_end, yl, cz + w + 1, "minecraft:stone_bricks")

    # 5) temple platform placeholder on the island
    add("# temple placeholder")
    setbox(cx - 10, yi + 1, cz - 10, cx + 10, yi + 1, cz + 10, "minecraft:gold_block")

    # 6) calibration markers (centre column, +X red, +Z blue)
    add("# markers")
    setbox(cx, yi + 1, cz, cx, yi + 8, cz, "minecraft:redstone_block")
    setbox(cx + 1, yl + 1, cz, cx + 6, yl + 1, cz, "minecraft:red_concrete")
    setbox(cx, yl + 1, cz + 1, cx, yl + 1, cz + 6, "minecraft:blue_concrete")
    return c, Z, R


def preview(cfg, Z, R, cols=79):
    """top-down design preview by true radius (independent of FAWE)."""
    w = cfg["canal_w"]

    def kind_at(dx, dz):
        rr = math.hypot(dx, dz)
        if rr > R:
            return " "
        k = " "
        for inner, outer, kd in Z:
            if (inner < rr <= outer) or (inner == 0 and rr <= outer):
                k = {"island": "@", "land": "L", "city": "C", "water": "~"}[kd]
        return k

    step = max(1, int(2 * R / cols))
    rows = []
    for dz in range(int(-R), int(R) + 1, step):
        row = []
        for dx in range(int(-R), int(R) + 1, step):
            ch = kind_at(dx, dz)
            if dx >= Z[0][1] and abs(dz) <= w and ch not in " @":
                ch = "="                                   # canal
            if abs(dx) < step and abs(dz) < step:
                ch = "+"                                   # centre
            row.append(ch)
        rows.append("".join(row))
    return "\n".join(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=BLOCKS_PER_STADE)
    ap.add_argument("--out", default="atlantis_30.commands")
    a = ap.parse_args()
    BLOCKS_PER_STADE = a.scale
    cmds, Z, R = emit(CFG)
    with open(a.out, "w") as f:
        f.write("\n".join(cmds) + "\n")
    heavy = sum(1 for l in cmds if l.startswith("//generate") or l.startswith("//set"))
    print(f"scale={a.scale} b/stade | outer radius={int(R)} | diameter={int(2 * R)}")
    print("zones (inner..outer, kind):")
    for inner, outer, kd in Z:
        print(f"   {int(inner):4d}..{int(outer):4d}  {kd}")
    print(f"commands: {len(cmds)} lines, {heavy} heavy ops -> {a.out}\n")
    print("TOP-DOWN DESIGN  (@=island L/C=land ~=water ==canal +=centre):\n")
    print(preview(CFG, Z, R))
