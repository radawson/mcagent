# Ships rig (v2) — boat physics, ancient hulls

Sailable and static ancient ships with no client mods. A rideable ship is a normal **oak boat**
(movement, steering, water physics) carrying a ship **`item_display`** (the shape) as its passenger.
A static ship is just the `item_display`, with no boat at all. Every model uses only **vanilla block
textures**, so there are no custom image files to ship.

Two hulls, and the difference between them is the point:

| | trireme (warship) | merchantman (round ship) |
|---|---|---|
| real length | ~37 m | **14 m** (Kyrenia wreck) |
| real beam | 6 m | **4.4 m** |
| ratio | **6.2 : 1** — a needle | **3.2 : 1** — a tub |
| tells | bronze ram, low, long | **no ram**, deep belly, square sail, quarter-rudders, deck cargo |

The trireme is proportioned off the standard reconstruction; the merchantman off the **Kyrenia**
wreck (4th c. BC, the best-preserved Greek merchant hull, found with ~381 amphorae aboard). The
namespace is still `trireme:` for continuity.

```
trireme/
  resourcepack/            <- clients load this (shows the models)
    pack.mcmeta
    assets/trireme/models/item/trireme.json      <- warship model (open in Blockbench to tune)
    assets/trireme/models/item/merchantman.json  <- trader model
    assets/trireme/items/trireme.json            <- item definitions (1.21.4+ system)
    assets/trireme/items/merchantman.json
  datapack/                <- goes in the world's datapacks/ (spawns + aligns the rigs)
    pack.mcmeta
    data/trireme/function/{summon,merchant,park,moor,moor_large,moor_at,tick,uninstall}.mcfunction
    data/minecraft/tags/function/tick.json
```

## Install

**Datapack** — datapacks load per **save**, not per dimension. `scratchpad` is a dimension folder,
so put this in the actual world save: `<server>/whirled/datapacks/trireme/` then `/reload`.
Functions are global, so `/function trireme:summon` still works while you're in scratchpad.

**Resource pack (server auto-push, chosen)** — zip the *contents* of `resourcepack/` (so `pack.mcmeta`
is at the zip root), host it somewhere the clients can reach, and in `server.properties`:
```
resource-pack=<url-to-the-zip>
resource-pack-sha1=<sha1 of the zip>
require-resource-pack=true      # optional; prompts/forces clients to load it
```
Restart (or use a plugin that hot-sets the pack). Clients are prompted on join. For a quick local
test you can instead drop the zip in your own `resourcepacks/` and enable it in Options.

## Use

```
/function trireme:summon      # rideable trireme     — board it and row       (scale  4.0)
/function trireme:merchant    # rideable merchantman — board it and sail      (scale  3.0)

/function trireme:park        # STATIC trireme, hauled out DRY in a ship shed (scale 12.0 = 36 m)
/function trireme:moor        # STATIC coaster, afloat alongside a quay       (scale  7.5 = 13.6 m)
/function trireme:moor_large  # STATIC deep-sea trader, afloat alongside      (scale 14.0 = 25.4 m)

/function trireme:uninstall   # removes every ship of every type
```

**Where to stand — this is not obvious and it matters.** Static ships inherit *your yaw*.

- **To moor**: stand on the quay deck and look **ALONG** the quay, *not* out to sea. Traders lie
  alongside to unload. Looking seaward berths her bow-on into the stone.
- **To park**: stand at the **head of the slipway** and face **down the shed, toward the water**.
  Triremes drew only ~1 m, so they were hauled out and stored **dry** — she sits on the slip, not
  in the water, which is why `park` has no sink offset and `moor` does.

## Tuning

**The one number worth eyeballing in-game is `sink` on the moored hulls.** It assumes our quay deck
sits 2 m above the sea (`dock_gen: quay_y = sl + m2b(2)`) and the hull wants ~1.3 m of draught. If
she rides high and shows keel, sink her further; if the deck is awash, raise her. Iterate **without
repacking** using the macro:

```
/function trireme:moor_at {scale:"7.5",sink:"-4.5"}
```

Other knobs:
- **Fit to the boat** (rideables): edit the `transformation` in `summon.mcfunction` / `merchant.mcfunction`.
- **Facing**: the models' bows are +X. If a hull points the wrong way relative to travel, add a 180°
  yaw via `left_rotation` in the transformation (quaternion `[0,1,0,0]`).
- **Shape**: open the model JSONs directly in Blockbench (File > Open Model). Plain cuboids.

### Why the scales differ (don't "fix" this to make them uniform)
- **merchant is 3.0, not 4.0.** The merchantman model is 1.81 blocks long where the trireme model is
  3.0. Rendering both at 4.0 would make the trader **60%** of the warship's length when the real
  ratio is **38%**. 3.0 gives a 5.4-block coaster that reads correctly beside a 12-block trireme.
- **park is 12.0, not 4.0** (fixed in v2 — it was a real bug). At 4.0 a parked trireme was **12 m**,
  and the ship sheds we built off the **Zea** excavation are **40 m**: a toy in a boathouse. True
  scale is 37/3.0 = 12.3. At 12.0 she's 36 m long with a 4.5 m beam — which fits the excavated 6 m
  shed with ~0.75 m either side. The archaeology confirms the hull proportions.
- **moor_large exists** because Kyrenia is the best-*preserved* merchantman, not the biggest — she
  was a coaster. Mixed tonnage makes a wharf read as a working port rather than a car park of
  identical hulls.

## Version-sensitive knobs (adjust if something errors on your exact MC version)
1. `pack_format` in both `pack.mcmeta` files — set to your version's numbers.
2. Boat id: modern MC uses `minecraft:oak_boat`; older uses `minecraft:boat{Type:"oak"}`. Update the
   summon/merchant/uninstall/tick selectors if needed.
3. Item model binding: this uses the 1.21.4+ `minecraft:item_model` component + `items/` definitions.
   On older versions, drop `items/*.json` and instead give the paper a `custom_model_data` and add
   `overrides` predicates on `assets/minecraft/models/item/paper.json`.
4. `moor_at` uses **function macros** (`$`-prefixed lines, 1.20.2+). If macros are unavailable, call
   `moor` / `moor_large` and edit the literals.

## Entity tags (ships are a family now)
`ship_boat` / `ship_disp` (rideable), `ship_parked` (dry), `ship_moored` (afloat). `tick.mcfunction`
is one line keyed on the generic tags, so it covers every rideable hull including future ones — which
is why `summon.mcfunction` had to gain those tags too. Legacy `trireme_*` tags are still accepted by
`uninstall`. Static ships are deliberately **not** ticked: no vehicle, rotation set once at summon.

## Known limitations (iterate on-server)
- The player is visible sitting in the boat. To hide the boat itself, add a transparent
  `assets/minecraft/textures/entity/boat/oak.png` to the resource pack (a fully-transparent PNG) —
  note this makes *all* oak boats invisible.
- Display↔boat pairing uses nearest-boat for yaw (correct because the display rides its boat). Fine
  for mixed fleets; if you ever see cross-talk, switch to explicit UUID linking.
- No animated oars yet (add as cuboids + a small tick animation later).
- Moored hulls don't bob. A slow sine on the display's translation via the tick tag would sell it.
