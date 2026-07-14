#!/usr/bin/env python3
"""
Atlantis WATERFRONT -- a TRADING port with a naval arsenal in it, not the other way round.

  "...the canal and the largest of the harbours were FULL OF VESSELS AND MERCHANTS coming from all
   parts, who, from their numbers, kept up a multitudinous sound of human voices, and DIN AND CLATTER
   of all sorts night and day."                                                  (PLATO_SOURCE §E)
  "The docks were full of triremes and naval stores."                            (PLATO_SOURCE §D)

BOTH exist -- but the noise, the crowds, the clatter is CARGO. v1 of this file took one beautiful
piece of archaeology (the Zea ship sheds) and turned the whole waterfront into a navy base. Rick
caught it: "These are trading docks, not war machine slots."

THE SHIP TYPES DEMAND DIFFERENT BERTHS, and that is the whole design:
  * TRIREME    -- narrow racing hull, ~37 m x 6 m, draught ~1 m. HAULED OUT and stored DRY up a
                  slipway, in a long low roofed shed (neosoikos). Excavated at Zea: 40 x 6 x 4.03 m.
  * MERCHANTMAN-- Phoenician/Greek "round ship": beamy, deep-drafted, sail-driven. STAYS AFLOAT,
                  moors ALONGSIDE, and gets UNLOADED. You cannot berth these two in one structure.

SO THE WATERFRONT IS TWO THINGS:
  NAVAL SEGMENTS  (minority, clustered) -- the neosoikoi. Slipways, ships drawn up dry. The arsenal.
  TRADING SEGMENTS (majority) -- a LOW OPEN QUAY built out into the water at ~2 m above the waterline
                  (you cannot unload a ship onto a wharf 8 m above its deck). Merchantmen alongside;
                  cranes, gangplanks, crates, amphorae. And the rock gallery BEHIND it becomes what it
                  should always have been: VAULTED BONDED WAREHOUSES. Cargo comes off the ship, across
                  the quay, into the vaults. The cave is the storage, not the berth.

    python3 dock_gen.py --ring 1 --sectors 32 --sector 1 --out dock_r1_s01.schem
    # //schem load dock_r1_s01 ; //paste -o -a     (gallery must already be carved 44 m deep)
"""
import argparse, math, random
from schem import write_schem
from vmodel import VModel

P = dict(
    face      = "minecraft:prismarine_bricks",
    face_dark = "minecraft:dark_prismarine",
    face_rough= "minecraft:prismarine",
    rock      = ["minecraft:calcite", "minecraft:granite", "minecraft:blackstone"],
    deck      = "minecraft:dark_oak_planks",
    post      = "minecraft:stripped_dark_oak_log[axis=y]",
    bollard   = "minecraft:waxed_cut_copper",
    ring      = "minecraft:chain[axis=y,waterlogged=false]",
    sea_lamp  = "minecraft:sea_lantern",
    lamp      = "minecraft:lantern[hanging=true,waterlogged=false]",
    paving    = ["minecraft:stone_bricks", "minecraft:andesite", "minecraft:polished_andesite"],
    vault     = "minecraft:stone_bricks",
    cargo     = ["minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]",
                 "minecraft:cut_copper", "minecraft:bricks", "minecraft:white_wool"],
    rope      = "minecraft:chain[axis=y,waterlogged=false]",
)

NAVAL_FRACTION = 0.30      # a minority. The rest is commerce -- that is the point.


def _rng(*key):
    h = 0
    for k in key:
        h = (h * 1000003) ^ (hash(k) & 0xFFFFFFFF)
    return random.Random(h & 0x7FFFFFFF)


def build_wedge(S, ring, sectors, sector, sea=-30, seed=4242):
    V = VModel(S, sea=sea)
    cx, cz, m2b = V.cx, V.cz, V.m2b
    rf, sl, y_land = V.ring_floor, V.sea, V.y_land

    r_in = V.r_w1 if ring == 1 else V.r_w2
    depth = V.dock_depth
    r_back = r_in + depth
    vault_roof = V.shed_roof                      # underside of the native-rock roof

    quay_w = m2b(14)                              # the working wharf, built OUT into the water
    quay_y = sl + m2b(2)                          # ~2 m above the waterline: unloading height
    r_quay = r_in - quay_w                        # outer edge of the wharf; ships moor here

    a0 = 2 * math.pi * sector / sectors
    a1 = 2 * math.pi * (sector + 1) / sectors

    B = {}
    def at(r, th, yy, blk):
        B[(cx + int(round(r * math.cos(th))), yy, cz + int(round(r * math.sin(th))))] = blk

    # ---- the wharf: a low quay running the whole waterfront, in front of everything ----------
    arc_all = max(8, int((a1 - a0) * r_in))
    for j in range(arc_all + 1):
        th = a0 + (a1 - a0) * j / arc_all
        g = _rng(seed, "quay", ring, sector, j)
        for si in range(quay_w + 1):
            r = r_quay + si
            for yy in range(rf, quay_y):                       # solid masonry mole
                at(r, th, yy, P["face_dark"] if yy < sl - 2 else P["face"])
            at(r, th, quay_y, g.choice(P["paving"]))           # the working deck
        if j % 7 == 3:                                          # sea lanterns in the quay face
            at(r_quay, th, sl - 2, P["sea_lamp"])
        if j % 9 == 5:                                          # bollards + mooring rings
            at(r_quay + 1, th, quay_y + 1, P["bollard"])
            at(r_quay + 1, th, quay_y + 2, P["ring"])

    # ---- segments: mostly trade, some navy ---------------------------------------------------
    seg_arc = max(40, m2b(60))
    nseg = max(1, int(round((a1 - a0) * r_in / seg_arc)))
    for k in range(nseg):
        sa = a0 + (a1 - a0) * k / nseg
        sb = a0 + (a1 - a0) * (k + 1) / nseg
        g = _rng(seed, "seg", ring, sector, k)
        if g.random() < NAVAL_FRACTION:
            _naval(at, V, g, r_in, r_back, sa, sb, m2b)
        else:
            _trading(at, V, g, r_in, r_back, r_quay, quay_w, quay_y, sa, sb, m2b)

    return B, V


# ---------------------------------------------------------------- the arsenal
def _naval(at, V, g, r_in, r_back, sa, sb, m2b):
    """Neosoikoi: long narrow low sheds, ships HAULED OUT up a slipway and stored dry (Zea)."""
    sl, rf = V.sea, V.ring_floor
    shed_w, pier_w = V.shed_width, V.shed_pier
    mouth, head, roof = V.slip_mouth, V.slip_head, V.shed_roof
    depth = V.dock_depth
    pitch = shed_w + pier_w
    n = max(1, int(round((sb - sa) * r_in / pitch)))
    for i in range(n):
        base = sa + (sb - sa) * i / n
        dp, ds = pier_w / max(1.0, r_in), shed_w / max(1.0, r_in)
        p0, p1 = base, base + dp
        s0, s1 = p1, p1 + ds
        for si in range(int(depth) + 1):
            r = r_in + si
            ramp = int(round(mouth + (head - mouth) * si / depth))
            for j in range(max(2, int(dp * r_back)) + 1):        # masonry pier between sheds
                th = p0 + (p1 - p0) * j / max(2, int(dp * r_back))
                for yy in range(rf, roof):
                    at(r, th, yy, P["face_dark"] if yy < sl - 1 else P["face"])
                at(r, th, roof, g.choice(P["rock"]))
            for j in range(max(3, int(ds * r_back)) + 1):        # the shed and its slipway
                th = s0 + (s1 - s0) * j / max(3, int(ds * r_back))
                for yy in range(rf, ramp + 1):
                    at(r, th, yy, P["face_dark"] if yy < sl - 2 else P["face_rough"])
                at(r, th, roof, g.choice(P["rock"]))
                if si % 9 == 5 and j % 4 == 2:
                    at(r, th, roof - 1, P["lamp"])
                if si == int(depth):
                    for yy in range(ramp + 1, roof):
                        at(r, th, yy, P["face"])
        at(r_back - 2, (s0 + s1) / 2, head + 1, P["bollard"])    # hauling gear at the head


# ---------------------------------------------------------------- the trading port
def _trading(at, V, g, r_in, r_back, r_quay, quay_w, quay_y, sa, sb, m2b):
    """Open wharf + VAULTED BONDED WAREHOUSES in the rock behind it. Cargo comes off the ship,
    across the quay, into the vaults. This is where the din and clatter lives."""
    sl, rf, y_land = V.sea, V.ring_floor, V.y_land
    roof = V.shed_roof
    depth = V.dock_depth
    arc = max(6, int((sb - sa) * r_in))

    # --- warehouse vaults: an arcade facing the quay, piers and bays down the rock gallery ---
    bay = max(8, m2b(11))
    nb = max(1, int(round((sb - sa) * r_in / bay)))
    for i in range(nb):
        b0 = sa + (sb - sa) * i / nb
        b1 = sa + (sb - sa) * (i + 1) / nb
        an = max(3, int((b1 - b0) * r_back))
        for si in range(int(depth) + 1):
            r = r_in + si
            for j in range(an + 1):
                th = b0 + (b1 - b0) * j / an
                at(r, th, sl + 1, P["vault"])                    # vault floor, above the water
                on_pier = (j in (0, an))
                if on_pier:                                       # piers between bays -- the arcade
                    for yy in range(sl + 2, roof):
                        # leave an ARCH open at the quay end so carts and porters get through
                        if si < 3 and yy < sl + 5:
                            continue
                        at(r, th, yy, P["vault"])
                elif si == int(depth):                            # back of the vault
                    for yy in range(sl + 2, roof):
                        at(r, th, yy, P["vault"])
                elif si > 3 and g.random() < 0.16:                # STORES: the cargo in the vaults
                    at(r, th, sl + 2, g.choice(P["cargo"]))
                    if g.random() < 0.4:
                        at(r, th, sl + 3, g.choice(P["cargo"]))
                at(r, th, roof, g.choice(P["rock"]))              # native-rock roof (§B)
                if si % 8 == 4 and j == an // 2:
                    at(r, th, roof - 1, P["lamp"])

    # --- the wharf itself: cargo, cranes, gangplanks ---
    for j in range(arc + 1):
        th = sa + (sb - sa) * j / arc
        if j % 11 == 3:                                           # a derrick crane on the quay edge
            rr = r_quay + 3
            for yy in range(quay_y + 1, quay_y + 7):
                at(rr, th, yy, P["post"])
            for k in range(1, 5):                                 # the boom, out over the water
                at(r_quay + 3 - k, th, quay_y + 6, P["deck"])
            for yy in range(quay_y + 2, quay_y + 6):              # the hoist
                at(r_quay - 1, th, yy, P["rope"])
            at(r_quay - 1, th, quay_y + 1, g.choice(P["cargo"]))  # a load, half-lifted
        elif j % 5 == 1:                                          # cargo stacked on the wharf
            rr = r_quay + 4 + (j % 5)
            at(rr, th, quay_y + 1, g.choice(P["cargo"]))
            if g.random() < 0.45:
                at(rr, th, quay_y + 2, g.choice(P["cargo"]))
        if j % 13 == 6:                                           # a gangplank out to a moored hull
            for k in range(3):
                at(r_quay - k, th, quay_y, P["deck"])

    # --- steps from the wharf up to the city (the land sits 8 m above the water) ---
    th_s = (sa + sb) / 2
    for k in range(int(y_land - quay_y) + 1):
        r = r_in + 4 + k * 2
        for w in range(-2, 3):
            at(r, th_s + w / max(1.0, r), quay_y + k, g.choice(P["paving"]))
            at(r + 1, th_s + w / max(1.0, r), quay_y + k, g.choice(P["paving"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=185)
    ap.add_argument("--ring", type=int, choices=(1, 2), default=1)
    ap.add_argument("--sectors", type=int, default=32)
    ap.add_argument("--sector", type=int, default=0)
    ap.add_argument("--sea", type=int, default=-30)
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"dock_r{a.ring}_s{a.sector:02d}.schem"
    B, V = build_wedge(a.scale, a.ring, a.sectors, a.sector, a.sea, a.seed)
    W, H, L, pal, origin = write_schem(B, out)
    print(f"WATERFRONT (trading port + arsenal) -- ring {a.ring}, sector {a.sector}/{a.sectors}")
    print(f"  ~{int((1-NAVAL_FRACTION)*100)}% trading wharf + bonded vaults, ~{int(NAVAL_FRACTION*100)}% trireme sheds")
    print(f"  waterline y={V.sea} | wharf deck y={V.sea + V.m2b(2)} | city y={V.y_land}")
    print(f"  {len(B)} blocks | {W}x{H}x{L} | {pal} palette -> {out}")
    print(f"  WEOffset {origin}  ->  //schem load {out[:-6]} ; //paste -o -a")
