#!/usr/bin/env python3
"""Recon the whirled Atlantis east causeway: does the corridor make clean landfall,
and is the jagged-peaks target a real massif or a lone spike? Uses mcbiome's live
locate oracle (zero chunk gen)."""
import mcbiome, math
CENTER = (43500, 21000)
PEAKS  = (45484, 21640)          # jagged_peaks anchor found earlier
ALPINE = ["minecraft:jagged_peaks", "minecraft:frozen_peaks", "minecraft:snowy_slopes",
          "minecraft:stony_peaks", "minecraft:windswept_gravelly_hills", "minecraft:windswept_hills"]
HIT = 64                          # nearest-dist <= HIT  => point sits in that biome (quart rounding)

dx, dz = PEAKS[0]-CENTER[0], PEAKS[1]-CENTER[1]
L = math.hypot(dx, dz); ux, uz = dx/L, dz/L
brg = math.degrees(math.atan2(dx, -dz)) % 360

def classify(points):
    """-> {p: 'ocean'|'alpine'|'land'}"""
    out = {}
    oc = mcbiome.locate_batch([(p, p[0], p[1], "#minecraft:is_ocean") for p in points])
    land = []
    for p in points:
        r = oc[p]
        if r and r[4] == 0: out[p] = 'ocean'
        else: land.append(p)
    best = {p: 10**9 for p in land}
    for b in ALPINE:
        res = mcbiome.locate_batch([((p, b), p[0], p[1], b) for p in land])
        for p in land:
            r = res[(p, b)]
            if r: best[p] = min(best[p], r[4])
    for p in land:
        out[p] = 'alpine' if best[p] <= HIT else 'land'
    return out

# --- corridor profile: center -> past the peaks ---
print("EAST CAUSEWAY corridor  center(%d,%d) -> peaks bearing %.0f deg, %d blocks\n" % (CENTER+(brg, L)))
cpts = [(round(CENTER[0]+ux*d), round(CENTER[1]+uz*d)) for d in range(0, 4401, 200)]
cc = classify(cpts)
sym = {'ocean': '~', 'alpine': '^', 'land': '#'}
prof = "".join(sym[cc[p]] for p in cpts)
print("  d=0 (city center) -> d=4400   ( ~ open water  # low land  ^ alpine/rocky )")
print("  " + prof)
# landfall = first land after leaving center's isle; first alpine
first_alpine = next((i*200 for i, p in enumerate(cpts) if cc[p] == 'alpine'), None)
ocean_run = sum(1 for p in cpts if cc[p] == 'ocean')
print("  ocean cells %d/%d (%.0f%% water along ray); first alpine at d=%s blocks"
      % (ocean_run, len(cpts), 100*ocean_run/len(cpts), first_alpine))

# --- massif extent map around the peaks anchor ---
print("\nMASSIF extent around (%d,%d)  step 400, +-1600  (^ alpine  # land  ~ water):" % PEAKS)
step, half = 400, 1600
coords = list(range(-half, half+1, step))
mp = classify([(PEAKS[0]+ax, PEAKS[1]+az) for az in coords for ax in coords])
alp = 0
for az in coords:
    row = ""
    for ax in coords:
        c = mp[(PEAKS[0]+ax, PEAKS[1]+az)]
        row += sym[c]; alp += (c == 'alpine')
    print("  " + row)
print("  alpine cells: %d/%d (%.0f%%)  -> massif spans ~%d blocks if contiguous"
      % (alp, len(coords)**2, 100*alp/len(coords)**2, half*2))
