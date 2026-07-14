# PLATO_SOURCE — the primary text (build corpus)

Source: Plato, **Critias** (~360 BCE), trans. Benjamin Jowett (1871, public domain).
Full text: Internet Classics Archive, https://classics.mit.edu/Plato/critias.html
Companion (island size/location, not reproduced here): Plato, *Timaeus* 24e–25d.

This file holds the build-relevant passages **verbatim** so both agents design against the primary
source, not a paraphrase. `PLATO_SPEC.md` is our engineering interpretation; where the two disagree,
this file is the authority on *what Plato said* and the SPEC records *what we chose to build*.
Reading notes at the bottom flag every place they currently diverge.

---

## §A — The concentric zones (Poseidon shapes the site)

> "...breaking the ground, inclosed the hill in which she dwelt all round, making alternate zones of
> sea and land larger and smaller, encircling one another; **there were two of land and three of
> water**, which he turned as with a lathe, each having its circumference equidistant every way from
> the centre, so that no man could get to the island, for ships and voyages were not as yet."

## §B — Bridges, canal, ring dimensions, walls, docks

> "First of all they **bridged over the zones of sea** which surrounded the ancient metropolis, making
> a road to and from the royal palace. ... And beginning from the sea they bored **a canal of three
> hundred feet in width and one hundred feet in depth and fifty stadia in length**, which they carried
> through to the outermost zone, making a passage from the sea up to this, which became a harbour...
> Moreover, they **divided at the bridges the zones of land** which parted the zones of sea, leaving
> room for a single trireme to pass out of one zone into another, and they **covered over the channels
> so as to leave a way underneath for the ships; for the banks were raised considerably above the
> water.** Now **the largest of the zones into which a passage was cut from the sea was three stadia in
> breadth, and the zone of land which came next of equal breadth; but the next two zones, the one of
> water, the other of land, were two stadia, and the one which surrounded the central island was a
> stadium only in width. The island in which the palace was situated had a diameter of five stadia.**
> All this including the zones and **the bridge, which was the sixth part of a stadium in width**, they
> surrounded by a **stone wall** on every side, placing **towers and gates on the bridges** where the
> sea passed in. The stone which was used in the work they quarried from underneath the centre island
> ... **One kind was white, another black, and a third red**, and as they quarried, they at the same
> time **hollowed out double docks, having roofs formed out of the native rock.** ... The entire circuit
> of the wall, which went round the outermost zone, they **covered with a coating of brass**, and the
> circuit of the next wall they **coated with tin**, and the third, which encompassed the citadel,
> **flashed with the red light of orichalcum.**"

## §C — The Temple of Poseidon (citadel centre)

> "...in the centre was a **holy temple dedicated to Cleito and Poseidon**, which remained inaccessible,
> and was **surrounded by an enclosure of gold**... Here was **Poseidon's own temple which was a stadium
> in length, and half a stadium in width, and of a proportionate height, having a strange barbaric
> appearance.** All the outside of the temple, with the exception of the pinnacles, they **covered with
> silver, and the pinnacles with gold.** In the interior ... the **roof was of ivory** ... **coated with
> orichalcum**; ... **statues of gold: ... the god himself standing in a chariot** — the charioteer of
> six winged horses — **and of such a size that he touched the roof of the building with his head;
> around him there were a hundred Nereids riding on dolphins**..."

## §D — THE RING PROGRAMME (restored in full)

**This section was previously truncated with ellipses, and the elided text turned out to hold the
single most important passage in the dialogue for how the city is ZONED.** Verbatim:

> "In the next place, they had **fountains, one of cold and another of hot water**, in gracious plenty
> flowing... They constructed buildings about them and planted suitable trees, also they made
> **cisterns**, some open to the heavens, others roofed over, to be used in winter as **warm baths**;
> there were **the kings' baths, and the baths of private persons, which were kept apart; and there
> were separate baths for women, and for horses and cattle**... Of the water which ran off they
> carried some to the **grove of Poseidon**, where were growing all manner of trees of wonderful
> height and beauty... while the remainder was **conveyed by aqueducts along the bridges to the outer
> circles**; and there were **many temples built and dedicated to many gods**; also **gardens and
> places of exercise, some for men, and others for horses, IN BOTH OF THE TWO ISLANDS formed by the
> zones; and IN THE CENTRE OF THE LARGER OF THE TWO there was set apart a RACE-COURSE OF A STADIUM IN
> WIDTH, and in length allowed to extend ALL ROUND THE ISLAND, for horses to race in.** Also there
> were **GUARDHOUSES at intervals for the guards, THE MORE TRUSTED OF WHOM were appointed to keep
> watch in THE LESSER ZONE, WHICH WAS NEARER THE ACROPOLIS, while THE MOST TRUSTED OF ALL had houses
> given them WITHIN THE CITADEL, near the persons of the kings.** **The docks were full of triremes
> and naval stores**, and all things were quite ready for use."

**READING — THE RINGS ARE RANKS.** Least-trusted guard on the OUTER land ring (L2), more-trusted on
the INNER (L1), most-trusted inside the CITADEL. The concentric plan is a **security gradient**, not
a decorative one. Rick arrived at exactly this by threat-modelling the docks, *before* we found the
passage. It also means the two land rings are **not residential** and **not interchangeable** — the
dense housing is in the belt (§E). See RING_SPEC.md.

## §B addendum — lines we had missed, and they matter

> "...making a passage from the sea up to this, which became a harbour, and **leaving an opening
> sufficient to enable the LARGEST VESSELS to find ingress.**"

Independently confirms the 300-ft canal: it is sized for **the largest ships afloat**, not for barges.

> "The stone which was used in the work they quarried from underneath the centre island, and from
> underneath the zones, **ON THE OUTER AS WELL AS THE INNER SIDE**... and as they quarried, they at the
> same time hollowed out **double docks**, having roofs formed out of the native rock. **Some of their
> buildings were simple, but in others they put together different stones, VARYING THE COLOUR TO
> PLEASE THE EYE, and to be a natural source of delight.**"

Two things. (1) The zones were quarried on **both faces**, so dock frontages exist on the outer AND
inner side of each land ring. (2) **The polychrome stonework is in the text.** Rick's instruction
("use all the colors of the minecraft stone... to make this look interesting, but consistent") is not
a liberty — it is Plato's own description, and it licenses the white/black/red palette.

## §E — The great outer wall and the dense city ring

> "Leaving the palace and passing out across the three [harbours] you came to **a wall which began at
> the sea and went all round: this was everywhere distant fifty stadia from the largest zone or
> harbour**, and enclosed the whole, the ends meeting at the mouth of the channel which led to the sea.
> **The entire area was densely crowded with habitations**; and the canal and the largest of the
> harbours were full of vessels and merchants coming from all parts..."

## §F — The great plain and its irrigation grid

> "...the country immediately about and surrounding the city was a **level plain** ... of an **oblong
> shape, extending in one direction three thousand stadia, but across the centre inland it was two
> thousand stadia. This part of the island looked towards the south**... [a ditch] **excavated to the
> depth of a hundred feet, and its breadth was a stadium everywhere; it was carried round the whole of
> the plain, and was ten thousand stadia in length.** ... **straight canals of a hundred feet in width**
> were cut ... through the plain ... **at intervals of a hundred stadia** ... cutting transverse
> passages from one canal into another..."

---

## Reading notes — divergences from PLATO_SPEC (to resolve)

These are the inconsistencies between the primary text and our current spec/generator. Flagged, not
silently changed — decisions belong to Rick.

1. **Land-ring widths (material).** §B states the zones, outer→inner: water **3**, land **3**, water
   **2**, land **2**, water **1**. So from the island outward the widths are **W1=1, L1=2, W2=2, L2=3,
   W3=3**. Our spec/generator uses **L1=1, L2=2** (land rings one stade too narrow each). Correcting to
   the text changes the **core city from ⌀23 → ⌀27 stades** (core radius 11.5 → 13.5).

2. **Great-wall radius (follows from #1).** §E puts the outer wall "fifty stadia from the largest
   zone." With the corrected core radius 13.5, the wall sits at **r = 63.5 stades** (metropolis ⌀127),
   not 61.5 / ⌀123 as the spec currently has.

3. **Temple width (material).** §C: the temple is "a stadium in length, and **half a stadium in
   width**" = 1 × 0.5 stade (≈185 × 92 m). Our spec says 1 stade × **1 plethron** (≈185 × 31 m) — i.e.
   ~3× too narrow. Correct to half a stade.

4. **Confirmed as-specified** (no change): three water + two land rings (§A); water rings **1/2/3**
   stades (§B, matches); canal 300 ft × 100 ft × 50 stades (§B, matches); white/black/red stone with
   brass/tin/orichalcum facings outer→citadel (§B, matches our palette); central gold enclosure (§C).

5. **Features the text confirms** (queued emitters): **trireme tunnels** through the land rings, roofed,
   "a way underneath for the ships," banks raised above water (§B); **double rock-cut docks** roofed in
   native rock (§B); **bridges** ⅙-stade wide with towers/gates (§B); **racecourse** a stade wide
   running around the larger land ring (§D); **hot & cold springs**, cisterns/baths, **grove of
   Poseidon**, aqueducts along the bridges (§D); the **great plain** 3000×2000 stades with a perimeter
   ditch and a 100-stade irrigation grid (§F).
