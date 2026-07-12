# TEMPLE_SPEC — the Temple of Poseidon

Owner: **[design]**. Authority: `PLATO_SOURCE.md` §C. Style decision (Rick): **Egypto-barbaric**.
Built as a handcrafted **schematic** (not `//generate`) — the "bulk by math, detail by schematic"
split. Parametric on `S` (blocks/stade), same as the city.

## 1. Why Egypto-barbaric (the reasoning, so it isn't relitigated)

- Plato calls it "**a strange barbaric appearance**" — explicitly *not* Greek.
- The footprint (1 × ½ stade = **185 × 92.5 m**, ~17,100 m²) is **~2× the largest Greek temple ever
  built** (Artemis at Ephesus, 129.5 × 68.6 m) and **~8× the Parthenon**. The real Temple of Poseidon
  at Sounion is 31 × 13.4 m — Plato's is ~40× its area. Nothing Greek approaches this.
- **No ancient roof spans 92 m.** Greek temples span 10–15 m. To roof this footprint you *must* fill
  it with columns — and Plato says exactly that: "the walls and **pillars** and floor." The hypostyle
  hall is structurally forced *and* textually attested.
- The only real precedent at this scale is Egyptian (Karnak's hypostyle: 134 columns) — and Solon got
  the tale from **Egyptian priests**. Most defensible reading available.

## 2. Dimensions (metres → blocks via `S/185`)

| Element | Real (m) | @S=185 | @S=30 |
|---|---|---|---|
| Length (1 stade) | 185 | 185 | 30 |
| Width (½ stade) | 92.5 | 92 | 15 |
| Pylon height | 35 | 35 | 6 |
| Nave roof (hypostyle centre) | 30 | 30 | 5 |
| Aisle roof | 20 | 20 | 3 |
| Column diameter | 4 | 4 | 1 |
| Column spacing (grid) | 12 | 12 | 2 |
| Wall thickness | 3 | 3 | 1 |
| Colossus height (head at nave roof) | 28 | 28 | 5 |
| Podium / steps | 2 | 2 | 1 |

Column count @S=185 ≈ 7 across × 15 along ≈ **~105 columns** (Karnak: 134). Right register.

## 3. Plan — Egyptian processional sequence (entrance faces **+X**, toward the grand canal/sea)

Along the long axis, entrance → sanctuary:

1. **Pylon** (~12% of length) — massive battered twin towers flanking the door. Silver-clad,
   gold pinnacles. The tallest exterior mass; the thing you see when you sail up the canal.
2. **Peristyle court** (~30%) — open to the sky, colonnaded on all four sides. Gold statues of the
   ten kings and their wives stand here (§C), plus the great **altar**.
3. **Hypostyle hall** (~35%) — roofed forest of orichalcum columns. **Raised central nave** with a
   clerestory (taller columns down the middle, light slotting in above the aisle roofs) — this is the
   Karnak move and it's what makes the interior feel enormous rather than merely dark.
4. **Sanctuary** (~23%) — the **colossus**: Poseidon standing in a chariot behind six winged horses,
   head touching the nave roof, ringed by **100 Nereids on dolphins**. Behind/beside it, the separate
   **inaccessible shrine of Cleito and Poseidon** inside its **enclosure of gold**, and the
   **orichalcum pillar** bearing the laws.

## 4. Material palette (Plato's own materials → blocks)

| Plato | Block | Note |
|---|---|---|
| Exterior "covered with silver" | `iron_block` + `polished_diorite` accents | metallic silver sheen |
| Pinnacles "with gold" | `gold_block` | akroteria / roof crest |
| Interior roof "of ivory" | `bone_block`, `white_terracotta`, `smooth_quartz` | |
| Walls, **pillars**, floor "coated with orichalcum" | **`waxed_cut_copper` / `waxed_copper_block`** | **waxed** — orichalcum must keep its red "flashing" colour, not oxidise green |
| Statues of gold (Poseidon, chariot, horses, kings) | `gold_block` | |
| Nereids on dolphins | `smooth_quartz` + `gold_block` accents | 100 of them, ringing the nave |
| Shrine enclosure of gold | `gold_block` | |
| Altar | `smooth_quartz` + `gold_block` | |

**Waxing is not decoration — it's a correctness requirement.** Unwaxed copper oxidises to green and
would destroy the orichalcum reading over time.

## 5. Build approach

- Generated in Python as a **`.schem`**, pasted at the citadel centre with `//paste -o` (the headless
  path proven by the original POC). Parametric on `S`, so one config change scales it.
- Sits on the citadel plateau (`y_isle`), replacing the current gold-slab placeholder.
- **@S=30 it will be cartoonish** (30 × 15 × 5) — that's expected and fine. We build a legible
  silhouette there (pylon mass, colonnade suggestion, gold roof crest, marker colossus). The real
  temple is an S=185 artefact, where a 30-block interior and ~105 columns actually land.

## 6. Deferred
Interior frescoes/reliefs, the grove of Poseidon, hot/cold springs and baths, the racecourse.
