# Trireme rig (v1) — boat physics, trireme shape

A sailable trireme with no client mods: a normal **oak boat** (movement, steering, water physics)
carries a **trireme `item_display`** (the shape) as its passenger. The display's model uses only
**vanilla block textures**, so there are no custom image files to ship.

```
trireme/
  resourcepack/            <- clients load this (shows the trireme model)
    pack.mcmeta
    assets/trireme/models/item/trireme.json   <- the model (open in Blockbench to tune)
    assets/trireme/items/trireme.json         <- item definition (1.21.4+ system)
  datapack/                <- goes in the world's datapacks/ (spawns + aligns the rig)
    pack.mcmeta
    data/trireme/function/{summon,tick,uninstall}.mcfunction
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
/function trireme:summon      # spawns a trireme at you; board it and row
/function trireme:uninstall   # removes all triremes
```

## Tuning (expected — this is v1)
- **Fit to the boat**: edit the `transformation` in `summon.mcfunction` — `translation` (lower/raise,
  centre) and `scale` (currently 2.4) so the hull sits at the waterline around the boat.
- **Facing**: the model's bow is +X. If it points the wrong way relative to travel, add a 180° yaw via
  `left_rotation` in the transformation (quaternion `[0,1,0,0]`).
- **Shape**: open `resourcepack/.../models/item/trireme.json` directly in Blockbench (File > Open Model)
  to refine the hull, add oar banks / shields, etc. It's authored as plain cuboids.

## Version-sensitive knobs (adjust if something errors on your exact MC version)
1. `pack_format` in both `pack.mcmeta` files — set to your version's numbers.
2. Boat id: modern MC uses `minecraft:oak_boat`; older uses `minecraft:boat{Type:"oak"}`. Update the
   summon/uninstall/tick selectors if needed.
3. Item model binding: this uses the 1.21.4+ `minecraft:item_model` component + `items/` definition.
   On older versions, drop `items/trireme.json` and instead give the paper a `custom_model_data` and
   add an `overrides` predicate on `assets/minecraft/models/item/paper.json`.

## Known v1 limitations (iterate on-server)
- The player is visible sitting in the boat. To hide the boat itself, add a transparent
  `assets/minecraft/textures/entity/boat/oak.png` to the resource pack (a fully-transparent PNG) —
  note this makes *all* oak boats invisible.
- Display↔boat pairing uses nearest-boat for yaw (correct because the display rides its boat). Fine for
  many triremes; if you ever see cross-talk, switch to explicit UUID linking (v2).
- No animated oars yet (add as cuboids + a small tick animation later).
