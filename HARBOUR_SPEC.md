# HARBOUR_SPEC — the waterfront, the canal, and the height of the rings

Supersedes the waterfront sections of PLATO_SPEC.md. Authority for *what Plato said* remains
PLATO_SOURCE.md; this file records *what we chose to build* and why.

Written after Rick flew the S=185 core and said: *"the land rings feel VERY cramped... having water
passages BEHIND the quay with no access is odd... at scale, how WIDE should the grand canal be?
Given the scale and grandeur of the temple, this feels sandwiched in."*

All three complaints turned out to be **one root cause**: we took Plato's **plan** dimensions
literally and then **eyeballed the third dimension and the programme**.

---

## 1. The canal was six times too narrow

> §B: *"beginning from the sea they bored **a canal of three hundred feet in width and one hundred
> feet in depth** and fifty stadia in length"*

A Greek stade is **600 feet**. So 300 ft = **half a stade = 92 m**, and 100 ft = **31 m**.

| | built | Plato |
|---|---|---|
| width | **15 m** | **92 m** |
| depth | 31 m | 31 m ✓ |

We had built a canal **deeper than it was wide** — a mineshaft, not a waterway. And Plato's grandest
single number, the one that makes the approach to the city an *event*, was the one we lost.

**How it survived:** `canal_w = 7` was a hardcoded half-width, not a derived one. Every other
dimension in the build passes through `m2b()`. This one didn't — and at **S=30**, the scale we
validated the engine at, `ft2b(300) = 15`, i.e. **half-width 7. It was correct.** It was calibrated
at the scale where it happened to be right, then frozen while S went to 185.

**Fix:** `ft2b()` now exists in `vmodel.py` so Plato's foot-measures survive as feet. `canal_w =
ft2b(300)`.

**And the coupling that hid it:** `tun_hw = canal_w - 1` — *one knob doing two jobs*. Fixing the
canal would have blown the trireme tunnels out to 91 m. The canal and the tunnels are different
things and **the text sizes them differently** (see §3). They are now independent.

---

## 2. The banks were a curb, not a bank

> §B: *"they covered over the channels so as to leave a way underneath for the ships; **for the banks
> were raised considerably above the water**"*

Built: land ring surface at **sea + 8 m**, tunnel headroom **sea + 6 m** — so the "native rock roof"
over a ship channel, carrying a road and a city, was **two metres thick**.

That is the cramped feeling, and it also quietly **forecloses a feature of the text**:

> §B: *"as they quarried, they at the same time **hollowed out double docks, having roofs formed out
> of the native rock**"*

**You cannot quarry a dock into an 8 m cliff.** The height is not decoration — it is the precondition
for the dock programme Plato describes.

**Fix — the rings STEP UP toward the centre** (Rick chose "masts up"):

| | surface | rock roof over the ship channel |
|---|---|---|
| outer land ring **L2** (3 stades wide) | **sea + 24 m** | 10 m |
| inner land ring **L1** (2 stades wide) | **sea + 36 m** | 22 m |
| **citadel** (5 stades diameter) | **sea + 55 m** | — |
| the belt (50 stades of dense city) | sea + 12 m | — |

Ship headroom in the tunnels is **14 m** — a merchantman passes through **with its mast up**.
Circuit walls now stand **8 m above their own ring**, so raising the rings no longer buries them.
The temple's pinnacle lands **~100 m above the sea**, and the city climbs to meet it instead of
lying flat around it.

`vmodel.py` now **asserts** the roof thickness at construction. The 2 m roof shipped because nothing
was checking; now a ring that is too short for its headroom raises at import.

---

## 3. The merchants were in the wrong rings — and defence is what proved it

Rick, arguing from **fortification**, not from Plato:

> *"it doesn't make sense to put docks with access up to the city in the OUTER walls — that would be
> a massive vulnerability... merchant cargo would want protection from raiders, pirates, and the sea
> itself."*

He was right, and the text says so twice:

> §B: the canal *"they carried through to **the outermost zone**, making a passage from the sea up to
> this, **which became a harbour**"*
>
> §E: *"**the canal and the largest of the harbours** were full of vessels and merchants coming from
> all parts... **din and clatter** of all sorts night and day"*

**The commercial harbour is W3, the outermost water ring** — walled in brass, entered only through
the gated canal mouth. Protected exactly as Rick argued.

And the clincher, which we had already quoted and never *read*:

> §B: *"leaving room for a **single trireme** to pass out of one zone into another"*

**You cannot run a cargo economy through a one-ship-at-a-time roofed tunnel.** That is not a trade
route. **It is a naval sally port.** So the interior rings are the navy's.

### The waterfront, inverted

| ring | programme |
|---|---|
| **W3** — outermost, 3 stades, brass wall, fed by the 92 m canal | **THE EMPORION.** Merchantmen afloat and alongside, cranes, bonded warehouses, din and clatter. |
| **W2, W1** — interior, reachable only by single-trireme tunnels | **THE ARSENAL.** Neosoikoi. Ships hauled out dry. "The docks were full of triremes and naval stores." |

This is Piraeus: **Kantharos** the commercial basin, **Zea** and **Mounichia** the naval ones,
physically separate. We arrived at it from Plato's own text plus Rick's threat model.

**The dead water Rick found behind the quay was never wrong** — it is a 44 m flooded gallery cut for
slipways, i.e. **the arsenal, in the right place, with the wrong tenant**. The trading port that was
floored over it moves out to W3; the neosoikoi move in.

### Which shore of W3 gets the cargo

W3 has two shores, and Rick's threat model decides:

- **Outer shore (r = r_w3, the city side) — the working wharves and the bonded warehouses.** The din
  and clatter. Backed by **50 stades of dense city**, not by an exposed outer wall. *This is where
  the cargo lives.*
- **Inner shore (r = r_l2, L2's outer cliff) — the official side.** Customs, the *deigma* (the
  sample-market), grand stairs up into the royal rings, the brass-crested wall on the skyline above.

---

## 4. "Double docks", read horizontally

> §B: *"they at the same time hollowed out **double docks**"*

Rick reads this as **two ships nose-to-tail in one gallery**, not two stacked levels — which is also
the standard reading of double *neosoikoi*.

**Fix:** arsenal gallery depth **44 m → 88 m** (two 40 m Zea sheds in line, plus the back wall).

---

## 5. What this costs

Raising the land rings from +8 to +24/+36 roughly **doubles the ring mass** (~+120M blocks at
S=185), and the 92 m canal is ~6× its old volume. Both are `//generate -r` annulus/box work, which
is the cheap path, but the build stream will need a **lower `--phase-every`** than the core run used.

Everything in this spec is **additive or an explicit overwrite** — no reliance on removal.
Per **INVARIANT 3**, the stale geometry (the 15 m canal's banks, the flooded trading gallery, the
buried wall tops) must be **explicitly re-set**, not merely un-emitted.
