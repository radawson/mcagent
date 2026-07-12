#!/usr/bin/env python3
"""
Temple of Poseidon generator -> Sponge v2 .schem (TEMPLE_SPEC.md).

Style: EGYPTO-BARBARIC (Rick's call). Egyptian processional sequence, because Plato's own
figures force it: 1 x 1/2 stade (185 x 92.5 m) is ~2x the largest Greek temple ever built, and
no ancient roof spans 92 m -- so the interior MUST be a hypostyle forest of columns, which is
exactly what Plato says ("the walls and PILLARS and floor... coated with orichalcum").

Plan, entrance (+X, facing the grand canal) -> back:
    PYLON  ->  PERISTYLE COURT (open sky, altar, gold kings)  ->  HYPOSTYLE HALL (raised nave +
    clerestory)  ->  SANCTUARY (colossus, 100 Nereids, Cleito's sealed gold shrine, laws pillar)

Parametric on S (blocks/stade). Sits on the citadel plateau, anchored to the SAME vertical model
as atlantis_cmds.py, and writes WEOffset = absolute min corner so `//paste -o` lands it exactly.

Usage:
    python3 temple_gen.py --scale 30 --out temple.schem
    # then, on the server:
    #   mc "//world scratchpad" ; mc "//schem load temple" ; mc "//paste -o -a"

NOTE: the colossus + Nereids are deliberately ABSTRACT MASSING (readable at distance, blocky up
close). Procedural statuary is the one thing that always looks worse than a hand-sculpt -- treat
them as correctly-scaled placeholders to hand-detail later. The ARCHITECTURE (pylon, colonnades,
~105-column hypostyle, roofs) is where procedural generation genuinely wins.
"""
import argparse, gzip, struct

STADE_M = 185.0
BUILD_FLOOR = -60          # must match atlantis_cmds.py
CX, CZ = -10000, 10000
DATA_VERSION = 4790        # match the live server (paper-current version.json)

PAL = dict(
    silver   = "minecraft:iron_block",              # "covered with silver"
    accent   = "minecraft:polished_diorite",
    gold     = "minecraft:gold_block",              # pinnacles, statues, shrine enclosure
    ivory    = "minecraft:smooth_quartz",           # roof "of ivory"
    ivory2   = "minecraft:white_terracotta",
    ori      = "minecraft:waxed_cut_copper",        # orichalcum -- WAXED so it never oxidises green
    ori2     = "minecraft:waxed_copper_block",
    quartz   = "minecraft:smooth_quartz",
)


# ---------------------------------------------------------------- NBT / schem writer (stdlib only)
def _s(v):
    b = v.encode("utf8")
    return struct.pack(">H", len(b)) + b

def t_int(n, v):    return b"\x03" + _s(n) + struct.pack(">i", v)
def t_short(n, v):  return b"\x02" + _s(n) + struct.pack(">h", v)
def t_barr(n, d):   return b"\x07" + _s(n) + struct.pack(">i", len(d)) + bytes(d)
def t_comp(n, inner): return b"\x0a" + _s(n) + inner + b"\x00"
def t_list0(n, et=10): return b"\x09" + _s(n) + bytes([et]) + struct.pack(">i", 0)

def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return out

def write_schem(blocks, path):
    """blocks: {(x,y,z): 'minecraft:foo[state]'} in ABSOLUTE world coords."""
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    mnx, mny, mnz = min(xs), min(ys), min(zs)
    W = max(xs) - mnx + 1
    H = max(ys) - mny + 1
    L = max(zs) - mnz + 1

    palette = {"minecraft:air": 0}
    data = bytearray()
    for y in range(H):                      # Sponge order: YZX
        for z in range(L):
            for x in range(W):
                b = blocks.get((mnx + x, mny + y, mnz + z), "minecraft:air")
                if b not in palette:
                    palette[b] = len(palette)
                data += _varint(palette[b])

    inner = (
        t_int("Version", 2)
        + t_int("DataVersion", DATA_VERSION)
        + t_comp("Metadata", t_int("WEOffsetX", mnx) + t_int("WEOffsetY", mny) + t_int("WEOffsetZ", mnz))
        + t_short("Width", W) + t_short("Height", H) + t_short("Length", L)
        + t_int("PaletteMax", len(palette))
        + t_comp("Palette", b"".join(t_int(k, v) for k, v in palette.items()))
        + t_barr("BlockData", data)
        + t_list0("BlockEntities")
    )
    with gzip.open(path, "wb") as f:
        f.write(t_comp("Schematic", inner))
    return W, H, L, len(palette), (mnx, mny, mnz)


# ---------------------------------------------------------------- the temple
def build(S):
    def m2b(m):
        return max(1, round(m * S / STADE_M))

    # vertical model -- identical to atlantis_cmds.py
    depth = m2b(30)
    sea = BUILD_FLOOR + depth
    y_isle = sea + m2b(20)          # citadel plateau
    y0 = y_isle + 1                 # temple sits on the plateau

    L = S                            # 1 stade long  (X, bow of the plan at +X)
    W = max(6, S // 2)               # 1/2 stade wide (Z)
    hl, hw = L // 2, W // 2

    podium   = m2b(2)
    aisle_h  = m2b(20)
    nave_h   = m2b(30)
    pylon_h  = m2b(35)
    wall_t   = m2b(3)
    col_d    = m2b(4)
    col_sp   = max(2, m2b(12))
    coloss_h = m2b(28)
    door_h   = m2b(20)

    x_front, x_back = CX + hl, CX - hl
    z0, z1 = CZ - hw, CZ + hw

    B = {}
    def fill(x1, y1, z1_, x2, y2, z2, blk):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1_, z2), max(z1_, z2) + 1):
                    B[(x, y, z)] = blk

    # --- 1. podium + steps -------------------------------------------------------------
    m = m2b(3)
    fill(x_back - m, y0, z0 - m, x_front + m, y0 + podium - 1, z1 + m, PAL["accent"])
    yf = y0 + podium                       # temple floor level
    fill(x_back, yf, z0, x_front, yf, z1, PAL["ori"])          # orichalcum floor

    # --- plan divisions (front -> back) ------------------------------------------------
    pylon_d = max(2, int(0.12 * L))
    court_d = max(3, int(0.30 * L))
    hyp_d   = max(3, int(0.35 * L))
    bx1 = x_front - pylon_d                # pylon: (bx1 .. x_front]
    bx2 = bx1 - court_d                    # court: (bx2 .. bx1]
    bx3 = bx2 - hyp_d                      # hypostyle: (bx3 .. bx2]
    #                                        sanctuary: [x_back .. bx3]

    # --- 2. perimeter walls (silver), behind the pylon ---------------------------------
    fill(x_back, yf + 1, z0, bx1, yf + aisle_h, z0 + wall_t - 1, PAL["silver"])
    fill(x_back, yf + 1, z1 - wall_t + 1, bx1, yf + aisle_h, z1, PAL["silver"])
    fill(x_back, yf + 1, z0, x_back + wall_t - 1, yf + aisle_h, z1, PAL["silver"])

    # --- 3. pylon: twin battered towers + tall doorway + gold pinnacles ----------------
    dw = max(2, W // 5)                    # doorway half-width
    fill(bx1, yf + 1, z0, x_front, yf + pylon_h, CZ - dw - 1, PAL["silver"])   # tower A
    fill(bx1, yf + 1, CZ + dw + 1, x_front, yf + pylon_h, z1, PAL["silver"])   # tower B
    fill(bx1, yf + door_h + 1, CZ - dw, x_front, yf + pylon_h, CZ + dw, PAL["silver"])  # lintel
    fill(bx1, yf + pylon_h, z0, x_front, yf + pylon_h, z1, PAL["gold"])        # gold pinnacles

    # --- 4. peristyle court: colonnade, altar, the ten kings & wives -------------------
    zc_a, zc_b = z0 + wall_t + 1, z1 - wall_t - col_d
    for x in range(bx2 + col_sp, bx1, col_sp):
        for z in (zc_a, zc_b):
            fill(x, yf + 1, z, x + col_d - 1, yf + aisle_h - 1, z + col_d - 1, PAL["ori"])
    xa = (bx1 + bx2) // 2                                                       # altar
    a = max(1, m2b(6))
    fill(xa - a, yf + 1, CZ - a, xa + a, yf + 1 + max(1, m2b(3)), CZ + a, PAL["quartz"])
    fill(xa - a, yf + 2 + max(1, m2b(3)), CZ - a, xa + a, yf + 2 + max(1, m2b(3)), CZ + a, PAL["gold"])
    kh = max(2, m2b(8))                                                          # 10 kings + 10 wives
    for i in range(10):
        kx = bx2 + 2 + int(i * (court_d - 4) / 9)
        for kz in (z0 + wall_t + col_d + 2, z1 - wall_t - col_d - 2):
            fill(kx, yf + 1, kz, kx, yf + kh, kz, PAL["gold"])

    # --- 5. hypostyle hall: column grid, raised nave, clerestory, ivory roof -----------
    nave_hw = col_sp                       # nave is ~2 bays wide
    for x in range(bx3 + col_sp, bx2, col_sp):
        for z in range(z0 + wall_t + col_sp, z1 - wall_t, col_sp):
            h = nave_h if abs(z - CZ) <= nave_hw else aisle_h
            fill(x, yf + 1, z, x + col_d - 1, yf + h - 1, z + col_d - 1, PAL["ori"])
    # roofs over hypostyle + sanctuary (court stays open to the sky)
    fill(x_back, yf + aisle_h, z0, bx2, yf + aisle_h, CZ - nave_hw - 1, PAL["ivory"])   # aisle roof
    fill(x_back, yf + aisle_h, CZ + nave_hw + 1, bx2, yf + aisle_h, z1, PAL["ivory"])
    fill(x_back, yf + nave_h, CZ - nave_hw, bx2, yf + nave_h, CZ + nave_hw, PAL["ivory2"])  # nave roof
    # (the band between aisle roof and nave roof at the nave edges is left OPEN = clerestory light)

    # --- 6. sanctuary: colossus, Nereids, Cleito's sealed shrine, the laws pillar ------
    xs = (bx3 + x_back) // 2
    colossus(B, PAL, xs, CZ, yf + 1, coloss_h, m2b)
    nereids(B, PAL, xs, CZ, yf + 1, max(3, m2b(18)), m2b)
    sh = max(3, m2b(10))                                                        # Cleito's shrine
    sx = x_back + wall_t + 2
    fill(sx, yf + 1, CZ - sh, sx + 2 * sh, yf + 1 + sh, CZ + sh, PAL["gold"])   # solid = inaccessible
    px = bx3 - max(2, m2b(6))                                                   # orichalcum laws pillar
    fill(px, yf + 1, CZ, px, yf + max(3, m2b(12)), CZ, PAL["ori2"])
    return B, dict(S=S, L=L, W=W, y0=y0, yf=yf, nave_h=nave_h, pylon_h=pylon_h, coloss_h=coloss_h)


def colossus(B, P, x, z, y, h, m2b):
    """Poseidon in a six-horse chariot, head at the nave roof. Abstract massing -- hand-detail later."""
    def fill(x1, y1, z1, x2, y2, z2, blk):
        for xx in range(min(x1, x2), max(x1, x2) + 1):
            for yy in range(min(y1, y2), max(y1, y2) + 1):
                for zz in range(min(z1, z2), max(z1, z2) + 1):
                    B[(xx, yy, zz)] = blk
    g = P["gold"]
    plinth = max(1, h // 12)
    fill(x - max(2, h // 6), y, z - max(2, h // 6), x + max(2, h // 6), y + plinth - 1,
         z + max(2, h // 6), P["quartz"])                                    # plinth
    b = y + plinth
    fill(x - 1, b, z - 2, x + 1, b + max(1, h // 10), z + 2, g)              # chariot car
    for i in range(6):                                                        # six winged horses (+X)
        hz = z - 5 + (i % 3) * 5
        hx = x + max(2, h // 8) + (i // 3) * max(2, h // 10)
        fill(hx, b, hz, hx + max(1, h // 10), b + max(2, h // 8), hz + 1, g)  # body
        fill(hx + max(1, h // 10), b + max(2, h // 8), hz, hx + max(1, h // 10),
             b + max(3, h // 6), hz + 1, g)                                   # neck/head
    legs = b + max(1, h // 10)
    torso_h = int(h * 0.45)
    fill(x - 1, legs, z - 1, x - 1, legs + int(h * 0.30), z - 1, g)           # legs
    fill(x + 1, legs, z + 1, x + 1, legs + int(h * 0.30), z + 1, g)
    t0 = legs + int(h * 0.30)
    fill(x - 2, t0, z - 2, x + 2, t0 + torso_h, z + 2, g)                     # torso
    fill(x - 2, t0 + torso_h - 2, z - max(4, h // 8), x + 2, t0 + torso_h, z + max(4, h // 8), g)  # arms
    fill(x - 1, t0 + torso_h + 1, z - 1, x + 1, t0 + torso_h + max(2, h // 12), z + 1, g)          # head


def nereids(B, P, x, z, y, r, m2b):
    """100 Nereids on dolphins, ringed around the colossus."""
    import math
    for i in range(100):
        a = 2 * math.pi * i / 100
        nx = x + int(r * math.cos(a))
        nz = z + int(r * math.sin(a))
        B[(nx, y, nz)] = P["quartz"]          # dolphin
        B[(nx, y + 1, nz)] = P["gold"]        # nereid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=30)
    ap.add_argument("--out", default="temple.schem")
    a = ap.parse_args()
    blocks, info = build(a.scale)
    W, H, L, pmax, origin = write_schem(blocks, a.out)
    print(f"Temple of Poseidon @ S={info['S']}  ({info['L']} x {info['W']} footprint)")
    print(f"  floor y={info['yf']}  nave roof +{info['nave_h']}  pylon +{info['pylon_h']}  colossus {info['coloss_h']} tall")
    print(f"  schem {W}x{H}x{L}, {len(blocks)} blocks, {pmax} palette entries -> {a.out}")
    print(f"  WEOffset (min corner) = {origin}  ->  paste with:  //schem load temple ; //paste -o -a")
