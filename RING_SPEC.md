# RING_SPEC — every ring is a different city

Rick, after the harbour argument: *"each of the rings has a unique set and style of buildings
(residential, administrative, military, core) and probably needs unique design."*

He was right, and then the primary text turned out to **say so explicitly**. PLATO_SOURCE §D — a
passage our own source file had truncated away with an ellipsis:

> *"gardens and places of exercise, some for men, and others for horses, **in both of the two islands**
> formed by the zones; and **in the centre of the larger of the two there was set apart a race-course
> of a stadium in width, and in length allowed to extend all round the island**, for horses to race
> in. Also there were **guardhouses at intervals for the guards, the more trusted of whom were
> appointed to keep watch in the lesser zone, which was nearer the Acropolis**, while **the most
> trusted of all had houses given them within the citadel**, near the persons of the kings."*

## THE RINGS ARE RANKS

Least-trusted guard on the **outer** land ring → more-trusted on the **inner** → most-trusted **inside
the citadel**. The concentric plan is a **security gradient**. It is the same logic Rick used to move
the merchants out to W3, arrived at independently, and it governs everything below.

**The two land rings are not residential.** The dense housing is in the **belt** (§E: *"the entire
area was densely crowded with habitations"*). Which means `city_radial.py` — terraces, tholoi,
round houses, the market — **is not wrong, it is aimed at the wrong zone.**

---

## The programme

| zone | r (stades) | width | what Plato puts there | character | generator |
|---|---|---|---|---|---|
| **CITADEL** | 0 – 2.5 | ⌀5 | Temple of Poseidon (1 × ½ stade), the gold enclosure of Cleito, the palaces, hot & cold springs, the kings' baths, **the grove of Poseidon**, the most-trusted guard | **SACRED + ROYAL.** Silver, gold, orichalcum. Monumental, inaccessible. | `temple_gen.py` ✓ · palace, grove, springs — TODO |
| **W1** | 2.5 – 3.5 | 1 | single-trireme passage | **ARSENAL** (innermost) | `dock_gen --naval` |
| **L1** | 3.5 – 5.5 | 2 | **guardhouses of the MORE TRUSTED guard**, gymnasia, gardens, *"many temples dedicated to many gods"* | **ELITE GUARD + ADMINISTRATIVE.** Disciplined, orthogonal, barracks in ranks. Tighter and more *ordered* than anything else in the city. | `ring_l1_gen.py` — NEW |
| **W2** | 5.5 – 7.5 | 2 | single-trireme passage | **ARSENAL** | `dock_gen --naval` |
| **L2** | 7.5 – 10.5 | 3 | **THE RACECOURSE** — a stade wide, running *all the way round*; gymnasia for men **and horses**; the less-trusted guard | **MILITARY-ATHLETIC / STATE.** Horse country. Vast and **OPEN**, the opposite of the belt. | `ring_l2_gen.py` — NEW |
| **W3** | 10.5 – 13.5 | 3 | *"the canal and the largest of the harbours were full of vessels and merchants... din and clatter night and day"* | **THE EMPORION** | `dock_gen --trading` (see HARBOUR_SPEC) |
| **BELT** | 13.5 – 63.5 | **50** | *"densely crowded with habitations"* | **RESIDENTIAL — the actual city.** Dense, organic, human. | **`city_radial.py`** — re-aimed here |

---

## The racecourse is a hard constraint, and it's glorious

> *"in the centre of the larger of the two... a race-course of **a stadium in width**, and in length
> allowed to **extend all round the island**"*

L2 spans 7.5 → 10.5 stades, so its centre line is **r = 9.0 stades**, and a stade-wide course runs
**r = 8.5 → 9.5**. At S=185 that is a **185 m wide track with a 10.5 km lap**.

It is not decoration — it **consumes the middle third of L2** and dictates the ring's whole plan:

```
r 7.5 ──── 8.5 ───────────── 9.5 ──── 10.5
  │ inner  │   RACECOURSE    │ outer  │
  │ band   │   185 m wide    │ band   │
  │ 1 st.  │   10.5 km lap   │ 1 st.  │
  gymnasia,     open sand,     stables,
  barracks,     turning posts, guardhouses,
  gardens       the spine      the W3 cliff
```

That alone turns L2 from "more generic city" into the thing you fly over and remember.

---

## Four distinct characters (the point of this document)

- **CITADEL** — monumental, sacred, silver/gold/orichalcum. Nothing repeats. Hand-placed.
- **L1** — *ordered*. Barracks in ranks, colonnades, temples. The most **regular** geometry in the
  build, deliberately, because it is the disciplined heart of the guard.
- **L2** — *open*. Dominated by the void of the racecourse. Stables, gymnasia, horse-country. The
  ring you can see across.
- **BELT** — *dense and organic*. Terraces, tholoi, one material per house, streets. `city_radial.py`
  already does this well; it just belongs out here.

The contrast between **L2's openness** and **the belt's density** — across the water of the great
harbour — is the single strongest urban move available to us, and we currently have neither.

**Bonus placement that falls out for free:** `city_radial.py`'s pomerium market was designed to back
onto the circuit wall. In the new scheme the belt's **inner** edge (r = r_w3) *is the emporion
shore*. So the market lands exactly where the ships unload. The pomerium market becomes the
**quayside market**, which is what an emporion *is*.

---

## Also in §D, and not yet built

- **Aqueducts along the bridges to the outer circles** — a run of arches on every bridge deck.
- **Hot and cold springs**, cisterns, roofed winter baths; the kings' baths and the private baths
  *"kept apart"*; separate baths for women, and for horses and cattle. (Citadel.)
- **The grove of Poseidon** — *"trees of wonderful height and beauty."* (Citadel.)
- **"Many temples dedicated to many gods"** — L1 and L2, not just the one on the citadel.
- **Guardhouses at intervals** — the module that ties L1 and L2 together, at two different grades.

---

## Rebuild, don't patch

Rick: *"the next run should be a complete rebuild, just to clear the remains of the intermediate
placing and cuts."*

**Correct, and it retires a whole class of risk.** Every fix in HARBOUR_SPEC and RING_SPEC would
otherwise have to fight **INVARIANT 3** (*idempotent re-runs fix CHANGED geometry, not REMOVED
geometry*) — the buried wall tops, the 15 m canal's banks, the floored-over trading gallery, the
city on the wrong rings. A `//set air` wipe to bedrock, then one clean stream, and **INVARIANT 3
stops applying at all**. Cheaper to reason about than any patch sequence we could write.
