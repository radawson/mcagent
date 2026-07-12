# PLATO_SPEC — Atlantis dimensional spec (authoritative)

Owner: **[design]** (Cowork). Source: Plato, *Critias* 113–121, via Rick's radial mapping.
This is the single source of truth for geometry. The generator (`atlantis_cmds.py`) builds
against these numbers; changes to dimensions happen here first, then in code.

## 1. Scale convention

One consistent scale factor drives everything, horizontal **and** vertical, so proportions
are always true.

- `1 stade = 185 m`, `1 plethron = stade/6 ≈ 30.8 m`, `1 ft = 0.3048 m`.
- `S` = **blocks per stade** (`BLOCKS_PER_STADE`). `blocks_per_metre = S / 185`.
- **Maquette scale `S = 30`** (current): a 1:6.2 model to validate engine + geometry. Low relief by design.
- **Final scale `S = 185`** (1 block = 1 m): true 1:1. Full verticality, ~22.7 km metropolis.

Any real dimension in metres → blocks = `m × S / 185`. All tables below give both.

## 2. Horizontal radial layout (from citadel centre)

| Zone | Width (stades) | Outer r (stades) | Outer r @S=30 | Outer r @S=185 |
|---|---|---|---|---|
| Citadel island | 5.0 ⌀ | 2.5 | 75 | 462.5 |
| Water ring 1 | 1.0 | 3.5 | 105 | 647.5 |
| Land ring 1 | 2.0 | 5.5 | 165 | 1017.5 |
| Water ring 2 | 2.0 | 7.5 | 225 | 1387.5 |
| Land ring 2 | 3.0 | 10.5 | 315 | 1942.5 |
| Water ring 3 | 3.0 | 13.5 | 405 | 2497.5 |
| **— core city ends (⌀27 stades) —** | | | **⌀810** | **⌀4995** |
| Outer inhabited belt | 50.0 | 63.5 | 1905 | 11747.5 |
| Great circuit wall | (at edge) | 63.5 | 1905 | 11747.5 |
| **— metropolis (⌀127 stades) —** | | | **⌀3810** | **⌀23495** |

Note: this **replaces** the placeholder `("city",3)` band in the current generator with the
true belt (`r 11.5–61.5`) + great wall at `r 61.5`.

## 3. Vertical model (datum = sea level, Z=0)

All three water rings sit at sea level. Values are design defaults (Plato fixes only the canal
depth; the rest are plausible and adjustable — see §8).

| Element | Real (m from sea level) | @S=30 | @S=185 |
|---|---|---|---|
| Water ring / canal floor | −30 (Plato: canal 100 ft) | −5 | −30 |
| Sea level (water surface) | 0 | 0 | 0 |
| Land ring surface (elevated) | +8 | +1 | +8 |
| Citadel plateau (cliff-topped) | +20 | +3 | +20 |
| Trireme tunnel headroom (inside land rings, water at Z=0) | ~8 tall | ~1 | ~8 |
| Bridge deck (ship clearance beneath) | +10 | +2 | +10 |
| Circuit wall height | +15 | +2 | +15 |
| Great outer wall height | +20 | +3 | +20 |

Maquette caveat: at S=30 the vertical collapses to ~1–5 blocks (low-relief model). The current
scratchpad build already approximates this (floor −60, sea −55). True relief appears at S=185.

## 4. Material palette (consistent, role-assigned)

Plato's own scheme is the organising principle: native **white / black / red** stone, faced with
three metals. Every element draws from ONE assigned sub-palette so the whole city reads as
deliberate, not noisy. Full use of the MC stone family for texture, keyed to fixed roles.

**Tri-colour native stone** (the signature banded cliffs & walls):

| Colour | Primary | Texture variants |
|---|---|---|
| White | `calcite` | `diorite`, `polished_diorite`, `smooth_quartz` |
| Black | `blackstone` | `polished_blackstone`, `deepslate`, `polished_deepslate` |
| Red | `granite` | `polished_granite`, `red_sandstone`, `red_nether_bricks` |

Banding rule: courses cycle **white → red → black** repeating, so citadel cliffs and circuit
walls always share one legible rhythm.

**Metal facings** (Plato's three walls, outer→inner):

| Wall | Metal (Plato) | Block |
|---|---|---|
| Great outer wall | brass | `gold_block` / `gilded_blackstone` |
| Middle circuit wall | tin | `iron_block` / `polished_diorite` trim |
| Citadel wall | orichalcum ("flashed red light") | `cut_copper` / `copper_block` |

**Structural neutrals** (assigned, not mixed):

- Quarried bedrock / foundations: `tuff`, `polished_tuff`, `cobbled_deepslate`.
- Roads & tunnel roofs: `smooth_stone`, `polished_andesite`, `tuff_bricks`.
- Rock-cut docks: `deepslate_bricks`, `polished_deepslate`, `stone_bricks`.
- Temple: `smooth_quartz` + `quartz_pillar`, copper/gold (orichalcum) interior.

**Accents** (sparing, for interest): `netherite_block` for dark metal inlays on the temple and
citadel gates; chiseled/polished variants for cornices. Accents are ≤5% of any surface.

## 4b. Structures

- **Three circuit walls** wrapping the land zones — tri-colour stone bodies + metal facings above.
- **Citadel**: leveled plateau with **sheer vertical cliffs** (banded tri-colour) into water ring 1.
- **Temple of Poseidon**: centre, footprint 1 stade × ½ stade = 185 × 92.5 m (§C)
  (@S=185: 185×92 blocks; @S=30: 30×15). Tall ("barbaric"), interior colossus. Placeholder now.
- **Trireme tunnels**: bored through each land ring at water level so ships pass hidden between
  water rings; the tunnel roof is the surface road.
- **Rock-cut docks**: hollowed into the inner faces of the land-ring walls.
- **High bridges**: span the water rings citadel-ward, raised for ships to pass under (§3).

## 5. Grand canal profile

| Property | Real | @S=30 | @S=185 |
|---|---|---|---|
| Length (ocean → outer water ring) | 50 stades (9.25 km) | 1500 | 9250 |
| Width | 300 ft (91.4 m) | 15 | 91 |
| Depth (below sea level) | 100 ft (30.5 m) | −5 | −30 |

Current build uses a **symbolic** canal (12 wide, short overshoot) per earlier decision; the
literal profile above is the target when we drop "symbolic".

## 6. Generation strategy (required at these radii)

The 30-scale run proved the failure mode: `//generate` over never-generated chunks bottlenecks on
worldgen, not block-setting. The metropolis belt (r→1845 @S=30, ~13k virgin chunks) makes this
mandatory:

1. **Pre-generate the footprint** (exec) — Chunky/WorldBorder over full radius *before* any fill.
2. **Tile large ops** (design) — emit big annuli (belt, foundation, walls) as chunk-aligned
   sub-selections so each op is bounded and restartable; never one op over the whole belt.
3. **Adaptive wait** (exec) — poll to true completion; a timeout pauses+flags, never advances.

## 7. Build status / roadmap

- ✅ Core skeleton (island + 3 water + 2 land rings), 30-scale, on-target & concentric.
- 🔄 Outer belt + great wall — replacing placeholder; needs tiling + pregen.
- ⬜ Vertical relief (elevated land rings, citadel cliffs), tunnels, docks, raised bridges.
- ⬜ Full-size temple; tri-colour circuit walls; literal canal.
- ⬜ Scale to S=185.

## 8. Open decisions (design defaults chosen; flag to change)

- Vertical elevations in §3 (land +8, citadel +20, wall heights) are my defaults — Plato is silent.
- Water-ring depth set equal to canal depth (−30 m) for trireme navigability.
- Tri-colour material picks in §4 are provisional block choices.
