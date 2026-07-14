#!/usr/bin/env python3
"""
Shared Sponge-v2 .schem writer (stdlib only -- no pip deps).

Used by temple_gen.py and city_gen.py. Writes BOTH the top-level `Offset` int-array AND the
Metadata WEOffset. The top-level Offset is AUTHORITATIVE: FAWE's `//paste -o` places the min corner
at it. With WEOffset alone, FAWE falls back to the opposite sign convention and pastes the build at
the NEGATED position (this cost us a mispasted temple -- see PROJECT_LOG).
"""
import gzip, struct

DATA_VERSION = 4790          # must match the live server (paper-current version.json / level.dat)


def _s(v):
    b = v.encode("utf8")
    return struct.pack(">H", len(b)) + b


def t_int(n, v):      return b"\x03" + _s(n) + struct.pack(">i", v)
def t_short(n, v):    return b"\x02" + _s(n) + struct.pack(">h", v)
def t_barr(n, d):     return b"\x07" + _s(n) + struct.pack(">i", len(d)) + bytes(d)
def t_comp(n, inner): return b"\x0a" + _s(n) + inner + b"\x00"
def t_list0(n, et=10): return b"\x09" + _s(n) + bytes([et]) + struct.pack(">i", 0)
def t_iarr(n, vals):  return b"\x0b" + _s(n) + struct.pack(">i", len(vals)) + b"".join(struct.pack(">i", v) for v in vals)


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


def write_schem(blocks, path, data_version=DATA_VERSION):
    """blocks: {(x,y,z): 'minecraft:foo[state]'} in ABSOLUTE world coords.
    Returns (W, H, L, palette_size, min_corner)."""
    if not blocks:
        raise ValueError("no blocks to write")
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    mnx, mny, mnz = min(xs), min(ys), min(zs)
    W = max(xs) - mnx + 1
    H = max(ys) - mny + 1
    L = max(zs) - mnz + 1

    palette = {"minecraft:air": 0}
    data = bytearray()
    for y in range(H):                        # Sponge order: YZX
        for z in range(L):
            for x in range(W):
                b = blocks.get((mnx + x, mny + y, mnz + z), "minecraft:air")
                if b not in palette:
                    palette[b] = len(palette)
                data += _varint(palette[b])

    inner = (
        t_int("Version", 2)
        + t_int("DataVersion", data_version)
        + t_comp("Metadata", t_int("WEOffsetX", mnx) + t_int("WEOffsetY", mny) + t_int("WEOffsetZ", mnz))
        + t_iarr("Offset", [mnx, mny, mnz])   # AUTHORITATIVE for //paste -o
        + t_short("Width", W) + t_short("Height", H) + t_short("Length", L)
        + t_int("PaletteMax", len(palette))
        + t_comp("Palette", b"".join(t_int(k, v) for k, v in palette.items()))
        + t_barr("BlockData", data)
        + t_list0("BlockEntities")
    )
    with gzip.open(path, "wb") as f:
        f.write(t_comp("Schematic", inner))
    return W, H, L, len(palette), (mnx, mny, mnz)
