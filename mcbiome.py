#!/usr/bin/env python3
"""
mcbiome.py -- seed-based biome/terrain SEARCH tool for mcmanager.

Finds sites matching terrain constraints (large ocean beside rocky land, etc.)
WITHOUT generating the world. It uses the running server's own generator as the
oracle via the vanilla `minecraft:locate biome` command, which samples the
biome-source climate noise at quart resolution and touches ZERO chunks. Because
it asks the live server, it is always exact for this world's version/seed -- no
need for cubiomes/Amidst to support the (far-future) data version.

Transport: SSH to the server, write commands to the console FIFO, scrape
logs/latest.log. Namespaced `minecraft:locate` is used so a plugin that shadows
the `/locate` alias (Essentials-style player locator) does not intercept it.

Primitives
----------
  locate(dim, x, z, target)   -> (concrete_biome, fx, fy, fz, dist) | None
      target may be a biome id (minecraft:deep_ocean) or a #tag (#minecraft:is_ocean).
  is_ocean(x, z)              -> concrete ocean biome id if (x,z) sits in ocean else None
      (tag locate returning dist 0 == the query point itself is that biome)

Everything is batched: one SSH round-trip fires a block of locate commands
(each tagged with a MARK token) plus a final sentinel, waits for the sentinel to
appear in the log, then returns the whole segment for parsing. Serial main-thread
execution guarantees output order == input order; the MARK tokens make parsing
robust against interleaved plugin log spam.
"""
import argparse, json, math, os, re, subprocess, sys, time

SSH_ALIAS = os.environ.get("SSH_ALIAS", "ptx-minecraft")
SRV       = os.environ.get("SRV", "/home/papercraft/papermc")
DIM       = os.environ.get("DIM", "minecraft:overworld")
PROBE_Y   = 64

# --- result-line grammar ---------------------------------------------------
# "The nearest minecraft:deep_ocean is at [-256, 64, -49616] (461 blocks away)"
# "The nearest #minecraft:is_ocean (minecraft:ocean) is at [40000, 64, 0] (0 blocks away)"
RE_HIT  = re.compile(
    r"nearest\s+(#?[\w:]+)(?:\s+\((#?[\w:]+)\))?\s+is at "
    r"\[(-?\d+),\s*(-?\d+),\s*(-?\d+)\]\s+\((\d+) blocks away\)")
RE_MISS = re.compile(r"Could not find")
RE_MARK = re.compile(r"\bMARK(\d+)\b")

# rocky / rough land palette (superset; absent biomes just return "Could not find")
ROCKY = [
    "minecraft:stony_peaks", "minecraft:jagged_peaks", "minecraft:frozen_peaks",
    "minecraft:snowy_slopes", "minecraft:windswept_hills",
    "minecraft:windswept_gravelly_hills", "minecraft:windswept_forest",
    "minecraft:stony_shore",
]


def locate_batch(queries, timeout=240):
    """queries: list of (key, x, z, target). Returns {key: (biome,fx,fy,fz,dist)|None}.

    No chat markers: `minecraft:locate biome` runs synchronously in command-dispatch
    order and emits exactly one result line each ("... is at [..] (N blocks away)" or
    "Could not find ..."). We wait until N such lines appear, then zip them to queries
    in order. (An extra "Locating element ... took N ms" line is emitted per locate but
    matches neither grammar, so it is ignored.)"""
    n = len(queries)
    lines = ["execute in %s positioned %d %d %d run minecraft:locate biome %s"
             % (DIM, x, PROBE_Y, z, target) for (key, x, z, target) in queries]
    remote = (
        'set -uo pipefail; cd "%s"; LOG=logs/latest.log; b=$(wc -l < "$LOG"); '
        'while IFS= read -r c; do printf "%%s\\n" "$c" > console.in; done; '
        't=0; while [ $t -lt %d ]; do '
        '  c=$(tail -n +$((b+1)) "$LOG" | grep -cE "blocks away\\)|Could not find"); '
        '  [ "$c" -ge %d ] && break; sleep 1; t=$((t+1)); done; '
        'tail -n +$((b+1)) "$LOG"'
    ) % (SRV, timeout, n)
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", SSH_ALIAS, "bash", "-c", remote],
                       input="\n".join(lines) + "\n", text=True, capture_output=True)

    # collect result/miss lines in order
    ordered = []
    for ln in p.stdout.splitlines():
        h = RE_HIT.search(ln)
        if h:
            tag_or_biome, paren, fx, fy, fz, dist = h.groups()
            ordered.append((paren or tag_or_biome, int(fx), int(fy), int(fz), int(dist)))
        elif RE_MISS.search(ln):
            ordered.append(None)
    out = {}
    for i, (key, *_ ) in enumerate(queries):
        out[key] = ordered[i] if i < len(ordered) else None
    return out


def nearest_rocky(x, z):
    """Return (biome, fx, fz, dist) for the closest rocky biome to (x,z), or None."""
    qs = [((b, x, z), x, z, b) for b in ROCKY]
    res = locate_batch(qs)
    best = None
    for b in ROCKY:
        r = res.get((b, x, z))
        if r and (best is None or r[4] < best[3]):
            best = (r[0], r[1], r[3], r[4])
    return best


# --- geometry --------------------------------------------------------------
def eastern_arc(radius, n=13):
    """Anchor points on the eastern semicircle: due-N (0,-r) sweeping E to due-S (0,+r).
    Excludes the western half (Minas Tirith). Returns list of (label, x, z)."""
    pts = []
    for i in range(n):
        az = math.pi * i / (n - 1)          # 0=N .. pi=S, going through E
        x = round(radius * math.sin(az))    # +x = east
        z = round(-radius * math.cos(az))   # -z = north, +z = south
        deg = round(math.degrees(az))
        pts.append(("az%03d" % deg, x, z))
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", choices=["anchors", "grid", "scan"], default="anchors")
    ap.add_argument("--box", type=int, nargs=4, help="scan: xmin xmax zmin zmax")
    ap.add_argument("--city-r", type=int, default=2497, help="scan: city footprint radius")
    ap.add_argument("--rmin", type=int, default=42000, help="scan: min dist from origin for candidates")
    ap.add_argument("--rmax", type=int, default=58000, help="scan: max dist from origin for candidates")
    ap.add_argument("--radius", type=int, default=50000)
    ap.add_argument("--anchors", type=int, default=13)
    ap.add_argument("--center", type=int, nargs=2, help="grid phase: cx cz")
    ap.add_argument("--half", type=int, default=3000, help="grid half-width (blocks)")
    ap.add_argument("--step", type=int, default=375, help="grid spacing (blocks)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.phase == "anchors":
        anchors = eastern_arc(a.radius, a.anchors)
        # one batch: for each anchor, nearest deep_ocean + nearest ocean(tag) + is_ocean@point
        qs = []
        for lbl, x, z in anchors:
            qs.append(((lbl, "deep"), x, z, "minecraft:deep_ocean"))
            qs.append(((lbl, "ocean"), x, z, "#minecraft:is_ocean"))
        res = locate_batch(qs)
        rows = []
        for lbl, x, z in anchors:
            deep = res.get((lbl, "deep"))
            oc   = res.get((lbl, "ocean"))
            at_ocean = bool(oc and oc[4] == 0)
            rk = nearest_rocky(x, z)
            rows.append(dict(label=lbl, x=x, z=z,
                             at_ocean=at_ocean,
                             ocean_biome=(oc[0] if oc else None),
                             ocean_dist=(oc[4] if oc else None),
                             deep_dist=(deep[4] if deep else None),
                             deep_at=([deep[1], deep[3]] if deep else None),
                             rocky=(rk[0] if rk else None),
                             rocky_dist=(rk[3] if rk else None),
                             rocky_at=([rk[1], rk[2]] if rk else None)))
        for r in rows:
            print("%-7s (%7d,%7d)  ocean@pt=%-5s %-22s d=%-5s  deep=%-6s  rocky=%-32s d=%s"
                  % (r["label"], r["x"], r["z"], r["at_ocean"],
                     r["ocean_biome"] or "-", r["ocean_dist"],
                     r["deep_dist"], r["rocky"] or "-", r["rocky_dist"]))
        if a.out:
            json.dump(rows, open(a.out, "w"), indent=2)
            print("wrote", a.out)

    elif a.phase == "grid":
        assert a.center, "--center cx cz required for grid phase"
        cx, cz = a.center
        step, half = a.step, a.half
        coords = list(range(-half, half + 1, step))
        qs = []
        for dz in coords:
            for dx in coords:
                x, z = cx + dx, cz + dz
                qs.append((("g", dx, dz), x, z, "#minecraft:is_ocean"))
        res = locate_batch(qs)
        grid = {}
        for dz in coords:
            for dx in coords:
                r = res.get(("g", dx, dz))
                grid[(dx, dz)] = bool(r and r[4] == 0)
        # ASCII map + centered ocean-disc radius
        print("ocean map (O=ocean . =land), center (%d,%d), step %d:" % (cx, cz, step))
        for dz in coords:
            print("".join("O" if grid[(dx, dz)] else "." for dx in coords))
        frac = sum(grid.values()) / len(grid)
        # Best inscribed city-center: the ocean cell whose clearance (distance to the
        # nearest LAND cell, capped by distance to the window edge since ocean may
        # continue beyond it) is largest = the deepest point in the basin.
        land = [(dx, dz) for (dx, dz), o in grid.items() if not o]
        best = None
        for (dx, dz), o in grid.items():
            if not o:
                continue
            dland = min((math.hypot(dx - lx, dz - lz) for lx, lz in land), default=1e9)
            dedge = half - max(abs(dx), abs(dz))
            clr = min(dland, dedge)
            if best is None or clr > best[2]:
                best = (dx, dz, clr)
        bx, bz = cx + best[0], cz + best[1]
        clr = int(best[2])
        print("ocean fraction %.0f%%" % (frac * 100))
        print("BEST city-center: (%d, %d)  inscribed ocean clearance ~%d blocks%s"
              % (bx, bz, clr, "  <-- fits r=2497 city" if clr >= 2600 else "  (tight for r=2497)"))
        rk = nearest_rocky(bx, bz)
        if rk:
            bearing = math.degrees(math.atan2(rk[1] - bx, -(rk[2] - bz))) % 360
            comp = ["N","NE","E","SE","S","SW","W","NW"][int((bearing + 22.5) // 45) % 8]
            print("nearest rocky landfall from city-center: %s at (%d,%d), %d blocks, bearing %.0f deg (%s)"
                  % (rk[0], rk[1], rk[2], rk[3], bearing, comp))
        if a.out:
            json.dump({"center": [cx, cz], "step": step, "half": half,
                       "grid": {f"{k[0]},{k[1]}": v for k, v in grid.items()},
                       "best_center": [bx, bz], "clearance": clr, "frac": frac,
                       "rocky": (list(rk) if rk else None)}, open(a.out, "w"), indent=2)
            print("wrote", a.out)

    elif a.phase == "scan":
        assert a.box, "--box xmin xmax zmin zmax required for scan phase"
        scan_phase(a)


def scan_phase(a):
    """Map ocean/land over a wide box, then rank candidate city-centers by
    OCEAN FRACTION within the city footprint (minimise land to carve) with a
    rocky coast at the rim (for the road). This is the honest 'find the best
    available site' pass -- no hand-picked anchors."""
    xmin, xmax, zmin, zmax = a.box
    step = a.step
    xs = list(range(xmin, xmax + 1, step))
    zs = list(range(zmin, zmax + 1, step))
    cells = [(x, z) for z in zs for x in xs]
    print("scan: %d cells (%dx%d) step %d" % (len(cells), len(xs), len(zs), step), flush=True)

    ocean = {}
    CH = 200
    for i in range(0, len(cells), CH):
        chunk = cells[i:i + CH]
        res = locate_batch([((x, z), x, z, "#minecraft:is_ocean") for (x, z) in chunk])
        for (x, z) in chunk:
            r = res[(x, z)]
            ocean[(x, z)] = bool(r and r[4] == 0)
        print("  classified %d/%d  (ocean so far %.0f%%)"
              % (min(i + CH, len(cells)), len(cells),
                 100 * sum(ocean.values()) / len(ocean)), flush=True)

    cr = a.city_r
    # candidate centers: every cell within [rmin,rmax] of origin, eastern (x>=0)
    scored = []
    for (cx, cz) in cells:
        r0 = math.hypot(cx, cz)
        if not (a.rmin <= r0 <= a.rmax and cx >= 0):
            continue
        near = [(x, z) for (x, z) in cells if (x - cx) ** 2 + (z - cz) ** 2 <= cr * cr]
        if len(near) < 4:
            continue
        frac = sum(ocean[c] for c in near) / len(near)
        scored.append((frac, cx, cz, r0, len(near)))
    scored.sort(reverse=True)

    # spatially de-dup the ranked list (keep centers > city_r apart)
    top = []
    for s in scored:
        if all(math.hypot(s[1] - t[1], s[2] - t[2]) > cr for t in top):
            top.append(s)
        if len(top) >= 8:
            break

    print("\nTop candidate city-centers by ocean-fraction within r=%d:" % cr)
    print("  %-18s %-6s %-8s %s" % ("center", "ocean%", "dist0", "nearest rocky coast"))
    out_rows = []
    for frac, cx, cz, r0, _ in top:
        rk = nearest_rocky(cx, cz)
        rk_s = ("%s @(%d,%d) %db" % (rk[0].split(":")[-1], rk[1], rk[2], rk[3])) if rk else "-"
        print("  (%7d,%7d)  %4.0f%%  %6d   %s" % (cx, cz, frac * 100, r0, rk_s))
        out_rows.append(dict(center=[cx, cz], ocean_frac=frac, dist0=r0,
                             rocky=(list(rk) if rk else None)))
    if a.out:
        json.dump(dict(box=a.box, step=step, city_r=cr,
                       ocean={f"{k[0]},{k[1]}": v for k, v in ocean.items()},
                       top=out_rows), open(a.out, "w"), indent=2)
        print("wrote", a.out)


if __name__ == "__main__":
    main()
