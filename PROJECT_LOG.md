# Atlantis build — project log

Write-access test from the Cowork design agent. If you can see this file in the repo,
Cowork can write here directly and will stop using the scratch outputs folder.

## Status
- Headless paste (schematic engine): PROVEN — POC landed on target, zero delta.
- Headless //generate engine: PROVEN at small scale — "14105 blocks have been created",
  true centered circle, default normalized coords correct on this build (no -r needed).
- Harness fixes applied (by the execution side):
  1. widen per-op wait to also match "blocks have been created" (//generate), not just
     "Operation completed" (//set).
  2. marker probe needs `execute in minecraft:scratchpad` (dimension context).
- Next: full 30-blocks/stade build, then BLOCKS_PER_STADE=180 (full stade), then features
  (agricultural plain + irrigation grid, bridges over each ring, harbour mouth).

## [exec] 2026-07-11 ~13:25 — 30-scale build COMPLETE + root cause of outer-op stalls

- Full 30-scale build landed at scratchpad -10000/10000. Centre marker ON TARGET
  (redstone -52..-45). All 7 zones concentric+centred, verified on +Z/-X/-Z:
  island(r40) water1(r90) land1(r120) water2(r165) land2(r225) water3(r300) city(r390),
  plus grand canal (+X), ring walls, temple gold+quartz, red(+X)/blue(+Z) arms. Outer edge void.
- ROOT CAUSE of the 4 "timed-out" outer ops: NOT a server error and NOT block-setting. Ops whose
  selection reaches the un-generated chunk frontier (r>~345 here) trip FAWE's large-edit gate:
  "Your selection is large (...N blocks). Use //confirm to execute". The op WAITS for //confirm;
  the harness never sent it -> false timeout. TPS stayed 20.0 throughout. Proven: sent //confirm
  manually -> "594457 blocks have been created", foundation then filled to r430.
  (Confirm trigger correlates with chunks-to-load, i.e. the frontier — water3 r345 completed w/o
  confirm because its chunks were already loaded; foundation r435 tripped it.)
- Recovery: re-ran the 3 remaining outer ops with //generate+//confirm — dirt 1,103,020 / grass
  220,604 / wall 108,960 blocks. //generate is idempotent over the same expression, so no teardown.
- TIMING for 180 planning: first op to touch the ~1000 virgin frontier chunks took ~240s (inline
  worldgen); subsequent ops on those chunks ran in ~9s. So worldgen is a real time cost at the
  frontier, but it is NOT a blocker — the //confirm gate was.
- HARNESS FIX (exec-owned, in run_commands.sh working tree, uncommitted): heavy-op loop now detects
  "Use //confirm" and acks it once, polls for real completion, and on a genuine stall it PAUSES +
  flags (exit 2) instead of silently advancing. Also: forceload centre chunk before the marker probe.
- REVISED fix list for 180 (was: pregen=mandatory/biggest-lever):
  1. [exec, DONE] harness //confirm handling — the cheap, robust correctness fix; no server change.
  2. [design] tiling of big zones/foundation/wall into chunk-aligned sub-ops — keeps each op bounded,
     restartable, and small enough to often stay UNDER the confirm/chunk-load threshold.
  3. [exec, optional] Chunky/WorldBorder pre-gen of the footprint before //generate — now a TIMING
     optimization (removes the ~4min inline worldgen stall + avoids tripping confirm), not the
     correctness fix. Worth it at full stade for predictability; not required for correctness.
- Git reconcile: mcagent/atlantis_cmds.py code == validated version (docstring-only diff, fine).
  run_commands.sh = cowork base + exec's forceload/confirm robustness. No blind overwrite survived.

## [design] 2026-07-11 — PLATO_SPEC + first-pass encode

- Added PLATO_SPEC.md (authoritative geometry/palette). Horizontal core matches the validated
  generator 1:1; adds literal metropolis (belt r11.5-61.5 + great wall r61.5, d123 stades) and the
  sea-level vertical model, structures, canal profile, generation strategy, palette.
- atlantis_cmds.py first-pass encode (design-owned):
  * scale factor S=BLOCKS_PER_STADE on 185 m/stade basis (maquette 30, final 185).
  * replaced placeholder ("city",3) with metropolis belt + great wall.
  * tri-colour native stone + metal facings (orichalcum=cut_copper / tin=iron / brass=gold),
    neutrals + <=5% netherite/copper accents.
  * per-zone base (no full-disc foundation) to cut op count.
  * DEFERRED: vertical relief, trireme tunnels, rock-cut docks, raised bridges, full temple.
- Root-cause correction noted: outer stalls were FAWE //confirm gate (exec fixed in harness),
  not chunk-gen. Recommendation: harness-only, NO server config change to the confirm threshold.
- TILING re-scoped: genuine bbox-bounding needs //generate -r world-coords (normalized breaks under
  tiled sub-selections). PREREQUISITE before S=185: validate -r coord origin on this build. Queued.
- HANDOFF to [exec]: at S=30, pre-generate the r=1845 footprint (Chunky) for timing, then run
  atlantis_cmds.py --scale 30 + run_commands.sh (confirm-aware). Paste the top-down preview +
  placement here. Belt is the heavy op; expect worldgen time, //confirm handled by harness.

## [design] 2026-07-11 — teardown + -r validation prepped

- Decision (Rick): //set air wipe the standing flat build BEFORE the metropolis rebuild.
- wipe_30.commands: single //set air over half-width ~545 bbox around -10000/10000, Y -60..-44
  (floor at -61 preserved). Run via run_commands.sh (its end marker-probe will report NOT found
  after a wipe -- expected, ignore).
- validate_r.sh: decisive two-test probe for //generate -r coordinate frame (absolute world vs
  region-relative min-corner). Off-centre selection with min corner at C; Test A world-coord disc,
  Test B local-coord disc; whichever makes C=stone identifies the frame. Prereq for real tiling@185.
- Suggested exec order this session: (1) run wipe_30.commands, (2) run validate_r.sh -> report A/B
  verdict, (3) run metropolis build (atlantis_cmds.py --scale 30) once ground is clear. Then [design]
  encodes tiling using the confirmed -r frame.

## [exec] 2026-07-11 ~14:00 — //generate -r origin VALIDATED (unblocks tiling)

- Ran the -r seam test in scratchpad: virtual centre world (400,400), circle r80, built in TWO
  adjacent chunk-aligned tiles (x350..450 and x450..550) with the SAME expression.
  Result: `//generate -r` uses ABSOLUTE WORLD COORDS. Tile A=51005, Tile B=12495 blocks; probe at
  (460,-57,400)=stone confirmed the circle is CONTINUOUS across the tile seam, r85=air (edge sharp).
- => The design prerequisite ("validate -r coord origin before tiling") is SATISFIED. Tiling the belt
  is unblocked. Validated recipe for tiled annulus fill (each tile = a pos1/pos2 sub-box + this expr):
    //pos1 <tileMinX>,<y1>,<tileMinZ>
    //pos2 <tileMaxX>,<y2>,<tileMaxZ>
    //generate -r minecraft:<block> (x-CX)^2+(z-CZ)^2<=Rout^2 && (x-CX)^2+(z-CZ)^2>Rin^2
  with CX=-10000, CZ=10000. Drop the `&&...>Rin^2` term for a solid disc. Tiles need NOT be centred
  on the city; the expression is world-anchored so any chunk-aligned tiling stitches seamlessly.
- BLOCKERS/STATE for the S=30 metropolis run:
  * Current atlantis_cmds.py emits the belt as ONE //generate over -11845..-8155 (3691x6x3691,
    ~40k virgin chunks). That single op cannot complete under MAXWAIT (inline worldgen ~hours) even
    with //confirm handled. Needs tiling (design, now unblocked) and/or pregen.
  * Chunky/WorldBorder are NOT installed on the server -> the "pregen with Chunky" step can't run as
    written. Pregen options: (A) install Chunky [server change, best for S=185 later], (B) exec builds
    a forceload-tiled pregen [no install], (C) skip pregen, tiled -r inline worldgen [~hours, no rush].
  * Inline worldgen rate observed ~3.6 chunks/s via //generate -> belt ~40k chunks ≈ 3h if not pregenned.
- HANDOFF to [design]: re-emit belt + great wall (+ any r>~345 annulus) as tiled -r ops per the recipe
  above (chunk-aligned, e.g. 512-block tiles). Then exec clears scratchpad (user chose fresh) + runs.
- Awaiting user decision on pregen approach (A/B/C) before the big run.

## [design] 2026-07-11 — belt re-emitted as tiled -r (unblocked)

- atlantis_cmds.py rewritten: ALL annulus fills now world-anchored `//generate -r` over chunk-aligned
  512 tiles (uniform path; dropped the normalized workaround now that -r=ABSOLUTE is validated).
  Per-tile ring-intersection skip -> thin annuli (water rings, great wall) emit only perimeter tiles;
  the belt tiles across ~r345..1845. Expression: (x+10000)^2+(z-10000)^2<=Rout^2[&&>Rin^2].
- No single mega-op remains; each tile is bounded + restartable. Tiling does NOT cut total chunk-gen.
- Added --maxr <blocks>: caps build radius for a fast SMOKE test in already-generated chunks
  (e.g. --maxr 400 rebuilds the core only) to validate the tiled emission before the ~3h belt.
- PREGEN recommendation (the gating fork): **A (install Chunky)** — endorse. Rick authorized it; it's
  the real timing fix (multithreaded, resumable) and MANDATORY at S=185 (~500k chunks, ~38h inline).
  C (inline, ~3h) is an acceptable no-install fallback for the S=30 maquette if Chunky prereqs fail.
  B (forceload pregen) not worth it — single-threaded, ~same rate as inline. Tiling ≠ timing fix.
- Suggested exec flow: wipe -> `--maxr 400` smoke (verify tiled core lands, seams continuous) ->
  install Chunky + pregen r=1845 -> full `--scale 30` build -> verify + paste preview/placement.

## [exec] 2026-07-11 ~17:06 — Chunky installed + footprint pre-generated

- Installed Chunky-Bukkit-1.5.3 (Modrinth, sha512-verified; lists MC 26.1.2 support). Server restarted
  cleanly (0 players; full load 74.8s), plugin enabled. Chunky targets the `scratchpad` world fine.
- Pre-generated the footprint: `chunky world scratchpad; center -10000 10000; shape circle; radius 1860;
  start` -> 55,225 chunks in 2:03 (~350-880 cps). vs ~3h if left to inline //generate.
- Verified on disk: scratchpad region files 41 -> 101; far-edge region r.-24.19.mca (~r1800) present;
  region X span -24..-16 brackets the r1860 footprint around centre region -20.
- STAGED for the S=30 metropolis build: footprint generated, Chunky available (reusable for S=185),
  -r validated, harness confirm-aware. BLOCKED ONLY on [design] re-emitting belt+great wall as tiled
  -r ops (recipe in the 14:00 entry). Once emitted: exec clears scratchpad (fresh) + runs + verifies.
- Chunky reusable at S=185: same commands, radius ~11400.

## [exec] 2026-07-11 ~17:30 — S=30 METROPOLIS BUILT (full, verified) + harness async-race fixed

- Ran wipe -> smoke -> full over the pre-generated footprint. FULL build: 229 heavy ops (222 tiled
  //generate -r + 7 //set), 0 stalls, ~75.76M blocks placed. PLACEMENT ON TARGET (-10000,-52,10000).
- Verified: great wall = complete gold ring r~1845 (3 axes); belt grass continuous to r1800; concentric
  at r1000 (3 axes); SEAM between two built belt tiles at x=-11264 (r1264) is grass E/ON/W = seamless.
- HARNESS BUG FOUND+FIXED (exec): FAWE edits are async; the old per-op "completion line after my
  snapshot" window raced the flush and FALSE-STALLED the smoke at op#10 even though the log showed 10
  completions for 10 ops. Rewrote run_commands.sh to COUNT cumulative completions vs heavy-ops dispatched
  (immune to flush ordering; still pauses+flags on a genuine stall). This would have broken the 229-op run.
- Vertical model @S=30 (low relief, as PLATO_SPEC §3 predicts): base tuff/deepslate -60, land/belt body
  stone-mix -60..-55, grass surface -54, water surface -55, citadel/circuit walls tri-colour to -51 with
  metal facings (cut_copper/iron/polished_diorite) -50, great wall gold -49, roads smooth_stone -53.
- Chunky pregen (55k chunks/2min) made the 75.76M-block build rip through in minutes. NOTE for S=185:
  same flow, pregen radius ~11400 (~500k chunks), tiled -r already validated.
- Ready for [design]: vertical relief + feature emitters (citadel cliffs, tunnels, docks, raised bridges,
  full temple, literal canal) per PLATO_SPEC roadmap. Skeleton is on-target & concentric.

## [design] 2026-07-11 — primary source added (PLATO_SOURCE.md) + 3 spec divergences found

- Added PLATO_SOURCE.md: build-relevant Critias passages verbatim (Jowett, public domain) as the
  authoritative text corpus. Reading against it surfaced 3 inconsistencies vs our spec/generator:
  1. LAND-RING WIDTHS: text gives (island-out) W1=1,L1=2,W2=2,L2=3,W3=3. Spec used L1=1,L2=2.
     Correcting -> core ⌀23 -> ⌀27 stades (core radius 11.5 -> 13.5).
  2. GREAT-WALL RADIUS: "fifty stadia from the largest zone" -> r=63.5 (metropolis ⌀127), not 61.5/⌀123.
  3. TEMPLE WIDTH: text = 1 stade x HALF a stade; spec said 1 stade x 1 plethron (~3x too narrow).
- Water rings (1/2/3), canal (300ft x 100ft x 50 stades), tri-colour stone + brass/tin/orichalcum
  facings, and the feature list (tunnels, docks, bridges, racecourse, springs, plain) all CONFIRMED.
- AWAITING Rick: adopt Plato's literal figures (correct spec + generator radii/temple) vs keep current.
  Recommend adopt (matches the "literal, full stade" intent). If yes, [design] updates PLATO_SPEC +
  atlantis_cmds.py radii; the tiled engine is unaffected (just different R values), re-run is cheap.

## [design] 2026-07-11 — literal Critias figures adopted (Rick)

- Updated PLATO_SPEC.md + atlantis_cmds.py to the primary text:
  * land rings -> 2 & 3 stades (island-out W1=1,L1=2,W2=2,L2=3,W3=3). Radii @S=30:
    island75 / w1=105 / l1=165 / w2=225 / l2=315 / w3=405 (core ⌀810 = ⌀27 stades).
  * great wall / belt outer -> r=63.5 stades = 1905 @S=30 (metropolis ⌀3810 = ⌀127).
  * temple footprint -> 1 stade x 1/2 stade = 30x15 @S=30 (was 21x21 placeholder).
- Engine unchanged (tiled -r); only R values differ. HANDOFF to [exec]: the standing S=30 build used
  the OLD radii -> needs wipe + rebuild. Chunky pregen was radius 1860; belt is now r1905 -> extend
  pregen to ~1920 (Chunky resumable, only the thin new ring). Then re-run + verify.
- PLATO_SOURCE.md is now the text authority; PLATO_SPEC records build choices; divergences reconciled.

## [design] 2026-07-11 — vertical relief encoded (parametric)

- atlantis_cmds.py: vertical model now PARAMETRIC on scale (block height = metres × S/185) off a
  sea-level datum, build floor pinned to Y=-60 at every S (never punches world floor -64).
  @S=30: floor -60, sea -55 (depth 5), land -54, citadel -52, circuit wall -53, great wall -52.
  @S=185: floor -60, sea -30 (depth 30), land -22, citadel -10, walls -15/-10 -> real relief.
  Water/canal cut to sea floor; land solid-filled -> cliffs & quays emerge for free.
- Marker: centre column now spans yf+1..y_isle+8 (full height) so the harness probe at PY=-52 still
  lands inside it after the vertical change -- NO harness edit needed (verify on smoke).
- GUARDRAIL for [exec]: solid land/water fills are cheap at S=30 but EXPLODE at S=185 (~1e10+ blocks).
  Do NOT run S=185 with this generator as-is. Before S=185, [design] must switch land/belt to
  surface+substrate+edge-quay (not solid to floor). TODO logged in the generator docstring.
- HANDOFF to [exec]: standing build uses old radii+flat model -> wipe + rebuild at S=30 (belt r1905,
  extend Chunky pregen to ~1920). Smoke --maxr 400 first to eyeball relief + confirm marker probe.

## [exec] 2026-07-11 ~19:00 — Rebuilt with corrected Plato radii (r1905)

- Synced [design] radius corrections (island75/w1 105/l1 165/w2 225/l2 315/w3 405; belt->1905,
  great wall r63.5=1905; temple 30x15). Engine unchanged, so just a re-run.
- Extended Chunky pregen 1860->1920 (resumable; +new band, 58,081 chunks total, +9s).
- Full wipe (wrote wipe_full.commands: //set air r1920 bbox Y-60..-44; the old wipe_30 only covered
  r545) -> rebuild. 242 heavy ops, 0 stalls (count-based harness held), ~80.72M blocks. ON TARGET.
- Verified NEW radii on +Z & -X: land1 r150, water2 r200, land2 r280, water3 r360, belt r450 all
  correct; great wall = gold ring relocated to r1905 (both axes). Concentric.
- BlueMap refreshed: save-all flush (clean, no watchdog this time) -> purge + update scratchpad;
  re-rendering the new build (~72 tiles/s). Map: http://10.10.12.5:8100 -> "scratchpad (metropolis)".
- Standing exec workflow for future rebuilds: pregen(if radius grew) -> wipe_full -> build ->
  verify -> save-all flush -> bluemap purge+update scratchpad.

## [design] 2026-07-11 — trireme tunnels + bridges emitted; trireme rig path fixed

- atlantis_cmds.py: added radial passages (§B). On the 3 cardinals that AREN'T the +X grand canal,
  each land ring gets a roofed trireme tunnel (channel floor -> water to sea -> ship headroom carved
  as air -> leftover land = roof -> smooth_stone road across the top), and each water ring gets a
  stone-brick bridge deck at sea+10m clearance. Parametric: real tunnels at S=185, token slots at S=30
  (only ~1 block between sea and land surface at maquette scale -- structure present, effect at 185).
  Params: tunnel half-width canal_w-1, road half-width ~S/12, headroom 6m, bridge clearance 10m.
  Toggle via CFG "passages" (default on); auto-skipped when maxr < r_w3 (smoke builds).
- HANDOFF to [exec]: rebuild to see passages (wipe_full -> build). Verify headless via block probes:
  e.g. on -X axis through land1, expect water at sea level and air above it (the tunnel), road at land
  surface; bridge deck (stone_bricks) over each water ring at bridge_y. Report a couple of probes.
- Trireme rig: README datapack path corrected to whirled/datapacks/ (per [exec]: datapacks load per
  save; scratchpad is a dimension). Plan endorsed: install datapack + summon + dump item_display
  transform telemetry so we tune scale/translation from real numbers; HOLD the server-wide resource
  pack until Rick gives an explicit go with the visual in front of him. pack_format set to 61 by [exec].

## [design] 2026-07-11 — rock-cut docks emitted; tunnel-depth question answered

- Tunnel DEPTH (Rick's check): already full sea-depth. Tunnel channel floor is pinned to yf=-60 with
  water to sea level -> 5 deep @S=30, 30 @S=185. Scales. The tight dim is HEADROOM (mast clearance):
  1 @S=30, 6 @S=185; raise tunnel roofs later if a full-scale mast needs >6.
- atlantis_cmds.py: rock-cut docks added -- covered water galleries carved into the INNER (unwalled)
  quay face of land rings L1 & L2 (moorage water yf+1..sea, covered slip air sea+1..sea+m2b(6), land
  above = roof). depth m2b(12) = 2 @S=30 / 12 @S=185. Outer-face + under-island docks deferred (would
  undercut circuit walls; thread around them later).
- HANDOFF to [exec]: rebuild + probe the docks: on any axis, just inside r_w1 (105) and r_w2 (225),
  expect water at sea level with air above (the covered slip) rather than solid land.
- NEXT (design): the full Temple of Poseidon (1x1/2 stade, silver walls/gold pinnacles, orichalcum
  interior, colossus) -- replacing the gold-slab placeholder. Then racecourse. Then S=185 fill-opt.

## [design] 2026-07-11 — Temple of Poseidon: spec + generator (schematic engine returns)

- TEMPLE_SPEC.md added. Style (Rick): EGYPTO-BARBARIC. Rationale is forced by Plato's own numbers:
  1 x 1/2 stade = 185 x 92.5 m (~17,100 m2) = ~2x the largest Greek temple ever (Artemis at Ephesus
  129.5x68.6) and ~8x the Parthenon; the real Poseidon temple at Sounion is 31x13.4. No ancient roof
  spans 92 m -> the interior MUST be a hypostyle forest, which is what Plato says ("walls and PILLARS
  and floor... coated with orichalcum"). Only precedent at that scale is Egyptian (Karnak, 134 cols),
  and Solon got the tale from Egyptian priests. "Strange barbaric appearance" = not Greek.
- temple_gen.py added: emits a Sponge v2 .schem via a SELF-CONTAINED stdlib NBT writer (no pip deps;
  DATA_VERSION=4790 -- [exec] please confirm against paper-current version.json). WEOffset = absolute
  min corner so `//paste -o` lands it exactly, reusing the POC's proven headless paste path.
- Plan (entrance +X, facing the grand canal): PYLON (twin towers, gold pinnacles) -> PERISTYLE COURT
  (open sky, altar, 10 kings + 10 wives in gold) -> HYPOSTYLE HALL (column grid, raised nave +
  open clerestory, ivory roof) -> SANCTUARY (colossus, 100 Nereids, Cleito's SEALED gold shrine,
  orichalcum laws pillar). ~105 columns @S=185.
- Orichalcum = **waxed** copper (waxed_cut_copper / waxed_copper_block). Correctness, not decor:
  unwaxed copper oxidises green and would destroy the "flashed with red light" reading.
- atlantis_cmds.py: gold-slab temple placeholder RETIRED (temple is now a schematic).
- HONEST NOTE: colossus + Nereids are abstract MASSING (correctly scaled, blocky). Procedural statuary
  always loses to a hand-sculpt -- treat as placeholders. The architecture is where procgen wins.
- HANDOFF to [exec]: `python3 temple_gen.py --scale 30 --out temple.schem`, scp to the FAWE schematics
  dir, then `//world scratchpad` ; `//schem load temple` ; `//paste -o -a`. Probe: pylon silver at the
  +X end, gold pinnacle course on top, orichalcum columns in the hypostyle, gold mass in the sanctuary.
  NB the city's centre marker column still runs up through the temple -- harmless, harness needs it.

## [design] 2026-07-11 — S=185 staged CORE-FIRST; fill-opt guardrail CORRECTED

- Offset bug was MINE: temple_gen wrote only Metadata.WEOffset, not the top-level Sponge `Offset`
  int-array, so FAWE used the opposite sign convention and mirrored the paste. [exec] fixed it with
  t_iarr("Offset",[min corner]). RULE: top-level `Offset` is authoritative; WEOffset alone is ambiguous.
- SCOPE (Rick): CORE FIRST at S=185. --core flag added (stops at water ring 3, r=13.5 stades = 2497,
  ~5 km ⌀). --tile added (use 256 at S=185: ~2.5M-block ops instead of ~10M).
  Core: ~19.6M columns, ~76k chunks (~3 min pregen), ~690M blocks. Belt deferred (see below).
- GUARDRAIL CORRECTED. I previously said "fill-opt required before S=185". Wrong -- it's required
  before the BELT, not the core. The core's land MUST stay solid: tunnels, docks and quay faces all
  need solid land at sea level; hollowing it would drain the tunnel water into the cavity. Making the
  water rings shallower saves nothing either (you swap water blocks for stone foundation, same volume).
- SAVE-FLUSH WATCHDOG: an OPS problem with an OPS solution -- do NOT compromise the geometry.
  Recommendation: build the S=185 core in PHASES with a `save-all` between each (per zone), so each
  flush is a fraction of the 690M delta. Optionally relax Watchdog max-tick-time for the build window
  (server config -> needs Rick's explicit go; staged saves alone should suffice).
- BELT (deferred, S=185): ~433M columns, ~1.7M chunks (~1 hr pregen), ~2.5e9 blocks, plausibly tens of
  GB of region files -- 95% of the build for 20 km of empty plain. It IS the place for
  surface+substrate+edge-quay (no water/tunnels there, so hollowing is safe). Disk check first.
  Generator is radial+tiled -> the belt is purely ADDITIVE, so core-first costs nothing later.

## [design] 2026-07-11 — #PHASE contract for staged saves (Rick: staged saves first, config only if needed)

- atlantis_cmds.py now emits `#PHASE <name>` markers at every natural boundary: each zone
  (zone-island-r*, zone-water-r*, zone-land-r*), then walls / canal / passages / docks / markers.
- They are COMMENT lines -> the current harness already skips them (backwards-compatible, no breakage).
- CONTRACT: **design owns where the boundaries are; exec owns what happens at one** (save / checkpoint
  / pause). To stage the S=185 core so no single flush carries the whole ~690M delta, [exec] can add a
  case to run_commands.sh BEFORE the generic `#` skip:

      \#PHASE*)
        echo "[phase] $line -- flushing save"
        b=$(mark); send "save-all flush"
        t=0; while [ $t -lt 180 ]; do
          tail -n +$((b+1)) "$LOG" | grep -q "Saved the game" && break; sleep 1; t=$((t+1))
        done
        echo "   saved (${t}s)"
        ;;
      \#*) continue ;;

- Plan: staged saves FIRST. Only if a phase flush still trips the 60s Watchdog kill do we touch
  Watchdog max-tick-time (server config -> would need Rick's explicit go).
- S=185 core commands:
    python3 atlantis_cmds.py --scale 185 --core --tile 256 --out atlantis_185_core.commands
    python3 temple_gen.py    --scale 185 --out temple185.schem
  Marker column spans -59..-2 @S=185, so the harness PY=-52 probe still lands inside it (no change).

## [design] 2026-07-11 — S=185 crashed the save; TWO corrections + the actual fix (ring depth)

- MY ERROR: I claimed a phase save would only write the zone that landed. Wrong in effect. BUT the
  reason matters: `save-all` writes only DIRTY chunks. The first phase save hit 75s because the WIPE
  (+fresh pregen) had dirtied the ENTIRE 76k-chunk footprint, so it carried everything. Staged saves
  aren't useless -- they were poisoned by the wipe in front of them. scratchpad is clean post-crash,
  so there is NO wipe to flush this time.
- CORRECTION TO OPTION B (fill-opt): it would BREAK the core. Hollowing land beneath the surface
  drains the trireme tunnels, rock-cut docks and quay faces into the cavity -- all three need solid
  land AT SEA LEVEL. And it wouldn't fix the save anyway: dirty CHUNK count stays 76k either way.
- THE ACTUAL FIX (option C, implemented): **ring depth**. Plato fixes the depth of exactly one thing --
  the CANAL, at 100 ft (~30 m). Ring depth was my invented number (I copied the canal's). Set rings to
  10 m (still deep water; a trireme draws 1-2 blocks) and keep the canal literally 100 ft:
    * yf (-60) stays the CANAL floor; new `rf = sea - m2b(10)` is the ring floor / city base.
    * @S=185: canal floor -60, ring floor -40, sea -30, land -22, citadel -10.
    * Core drops ~690M -> ~300M blocks (2.3x) with EVERY feature intact (tunnels/docks/quays sit at
      sea level, above rf). More faithful to the text, not less.
  All zone/wall/tunnel/dock fills rebased yf -> rf. Canal keeps the deep literal trench. Marker column
  still starts at yf+1 so the harness PY=-52 probe is unchanged. temple_gen needs NO change (same sea).
- PLAN: measure, don't guess. Build ONE zone (island) with a phase save and REPORT the save time.
  If it's a few seconds, run the rest staged, no config change. Only if a phase flush approaches the
  60s kill do we raise Watchdog max-tick-time for the build window (Rick's call).
- Do NOT wipe first (scratchpad is already clean) -- the wipe is what caused the crash.

## [design] 2026-07-11 — MEASURED save model -> bounded-delta flushes (--phase-every)

- [exec] MEASURED: save cost = **~7s baseline + dirty_chunks/200**. Island (2,600 chunks) = 20s.
  Extrapolated per-zone: land1 ~44s, water2 ~61s, land2 ~120s, water3 ~157s -> the big zones CRASH.
- MY ERROR (again): the ring-depth change cut BLOCKS, not CHUNKS. It made the build faster/lighter and
  is still the more faithful reading of Plato -- but it did nothing for the save. Save cost is chunks
  touched, full stop. Same reason the old fill-opt (option B) never would have fixed it either.
- ROOT ISSUE IS GRANULARITY, NOT CONFIG. Total work is fixed (~76k chunks / 200 = ~380s of writing).
  The only question is whether it lands in lumps big enough to kill. #PHASE was per-ZONE, and zones are
  wildly unequal (water3 = 30k chunks in one lump).
- FIX (design): `--phase-every N` inserts a #PHASE marker every N heavy ops, BOUNDING the dirty delta.
  With --tile 256 and --phase-every 24: ~3k chunks/flush -> ~25s each, ~20 flushes, ~9 min total.
  Never within 30s of the 60s kill. Watchdog stays ARMED. No config change. No geometry compromise.
- REJECTED option 3 (async auto-save, no forced flush): non-deterministic, and its failure mode only
  appears at the END -- if auto-save hasn't kept pace the final flush is the same 150s crash, and
  BlueMap stays dark until then.
- COMMAND: python3 atlantis_cmds.py --scale 185 --core --tile 256 --phase-every 24 --out atlantis_185_core.commands
  Island is already built+persisted; continue from there. [exec]: tune --phase-every off the measured
  model if flushes drift (target ~25s, hard ceiling 40s).

## [design] 2026-07-11 — RESOLVED: raise the Watchdog. The config was the miscalibration, not the code.

- 3rd crash. [exec] found the BOTTOM layer: `save-all flush` BLOCKS the main thread for its whole
  duration. So even a "healthy" bounded 25s flush is a 25s TICK FREEZE. ~20 of them during a huge
  build, stacked with concurrent FAWE work, eventually exceeds the 60s Watchdog kill. No flush cadence
  can fix a per-flush freeze that is inherently 20-30s.
- MY ERROR PATTERN (worth keeping): I refined three layers -- block count -> chunk count -> flush
  granularity. Each refinement was CORRECT and each hit the next constraint down. But I kept refusing
  the one lever that touched the binding constraint, because I framed it as "disabling the safety net".
  WRONG FRAME. The Watchdog is a DEADLOCK detector: its job is to catch a server that has hung and will
  never recover. A 25s save that COMPLETES is not a hang. The 60s default is tuned for gameplay ticks,
  not for a legitimate admin op on a large multi-world save. Raising it doesn't hide a bug -- it stops
  a liveness detector from misclassifying honest work. Sometimes the miscalibration is in the CONFIG.
- DECISION (Rick pre-authorized: "try staged saves first, and if that still breaks the watchdog, we can
  relax the settings"). Trigger fired. Plan:
  1. spigot.yml `settings.timeout-time: 300` (NOT -1 -- raise, don't disable; still catches a true
     deadlock, 10x headroom over the worst observed ~30s freeze). Restart.
  2. KEEP the bounded flushes (--phase-every 24). They cap each freeze at ~25s (server stays broadly
     responsive) and persist progress incrementally, so a failure costs one interval, not the build.
  3. The harness's own stall-detection (pause-and-flag) stays armed -- that is the real in-build guard,
     independent of the Watchdog.
  4. Re-run from the island. Then RESTORE timeout-time: 60 and restart.
- Lesson for the belt/future scale-ups: budget the save cost up front. Model: ~7s + chunks/200, and
  every flush is a main-thread freeze of that length.

## [design] 2026-07-12 — RECORD CORRECTION (2 crashes, not 3) + log-rotation bug + belt save budget

- CORRECTION to my entry above: there were **TWO** Watchdog crashes, not three. Getting this right
  matters because each has a DIFFERENT fix; folding them together would have us "fixing" a save path
  that was never broken.
    1. CRASH (real): 309M-block wipe -> 75s save > 60s Watchdog.        Fix: no wipe.
    2. CRASH (real): bounded-flush save STILL >60s stacked w/ FAWE work. Fix: Watchdog -> 300.
    3. NOT A CRASH: server was healthy throughout; 21 ops were on disk before the harness cried stall.
- BUG 3 (exec, fixed): Paper's size-based rotation rolled `latest.log` mid-build. The harness's
  cumulative completion counter used an ABSOLUTE line offset, which pointed past EOF of the fresh
  (short) file -> count read 0 -> FALSE STALL. Fix: bank the EXACT completion count from each
  rotated-away `.gz` so the count spans rotations (estimating is unsafe: under-count re-stalls,
  over-count silently skips ops). VALIDATED IN FLIGHT: rotation 2026-07-12-13.log.gz fired at
  18:03:03 and the build counted straight through it (ops #91/#94/#97 completed post-roll).
- BUG CLASS worth remembering: **state that assumes a stable frame of reference underneath it.** Same
  family as the earlier per-op log-snapshot race (fixed with a cumulative counter) -- then the
  cumulative counter itself assumed the log never moves. Ask "what is my offset relative to, and can
  that move?"
- BELT SAVE BUDGET (banked, do not lose): `--phase-every 24` was sized for a 60s Watchdog. With the
  Watchdog at 300, it is OVER-CONSERVATIVE: 64 saves x ~7s fixed baseline = ~7.5 min of pure overhead
  to cap freezes at 25s when we have 300s of headroom. For the BELT (dirty-chunk count ~20x worse),
  raise --phase-every substantially -- size each flush to land comfortably under ~200s (not 25s) using
  the measured model (~7s + chunks/200). Fewer, fatter flushes are strictly cheaper.

## [design] 2026-07-12 — S=185 CORE COMPLETE (the pylon is standing) + two invariants to keep

- DONE: the ~5 km full-stade core is built and the Temple of Poseidon is pasted on the citadel.
  1,378 heavy ops, 64 phase saves, one live log rotation AND a mid-build server restart -- zero blocks
  lost. Watchdog restored to 60. View: /tp @s -10000 30 10000 in scratchpad, or BlueMap at
  http://10.10.12.5:8100 (x -10000, z 10000).
- Final harness bug (benign, fixed by [exec]): `//paste` reports "has been pasted", which the DONE
  pattern didn't match -> added. Same bug class AGAIN (a completion contract that didn't cover every
  op type). Total: 2 real Watchdog crashes; 3 harness bugs; 0 design/geometry faults at S=185.

### INVARIANT 1 (design, HARD RULE) — every op in a build stream must be IDEMPOTENT + ABSOLUTELY ANCHORED
  This is what let the harness survive a full mid-build server restart: re-sending ops HEALED the build
  instead of corrupting it. It emerged from the tiling + headless-paste work rather than being designed
  for restart-tolerance -- but it is now a rule, not an accident.
    ALLOWED : //generate -r <fixed world-coord expr>, //set on absolute //pos1//pos2 boxes,
              //paste -o (origin baked into the schem).
    BANNED  : anything relative or stateful -- //paste at a position, //stack, //undo, player-relative
              selections. A restart landing inside a non-idempotent op is unrecoverable.

### INVARIANT 2 (ops) — BUILD LOCK before any long run
  The 18:03 restart was NOT issued by the build; most likely a parallel plugin-deploy
  (plugins/update/ + systemctl restart) landing mid-build. Idempotency made it survivable; that is a
  property of the command stream, not a guarantee about the world. FIX: harness drops
  `papermc/BUILD_IN_PROGRESS` at start, removes it at exit; the deploy path refuses to restart while it
  exists. Converts "we got away with it" into "it cannot happen." Do this BEFORE the belt run.

- REMAINING: hand-sculpt the colossus (procedural massing is the weak spot), racecourse, grove +
  hot/cold springs, outer-face & under-island docks, trireme fit-tuning, and the belt (see save budget).

## [design] 2026-07-12 — IN-GAME REVIEW (Rick flying, Cowork watching via computer-use): 2 canal bugs

- Bridges/passages on -X: **CORRECT**. Confirmed visually at X=-10607 (r~607, water ring 1): a proper
  wide stone-brick deck spans the water. radbox emits a flat slab as designed.
- CANAL BUG 1 (roof at water level): the canal filled water only to sea level and stopped. Where it
  crosses a LAND ring the land above the waterline (sea+1..y_land) was left SOLID -> the canal was a
  SUBMERGED BORE with its roof one block above the water. Rick swam it and read it exactly right.
  FIX: carve air from sea+1 up past y_land and the circuit walls -> an open channel to the sky (also
  gives Plato's "gates ... where the sea passed in").
- CANAL BUG 2 (two walls in the sea): quay walls ran the canal's FULL length, including across the
  open water rings, standing in the sea retaining nothing.
  FIX IS SUBTLE -- my first attempt was HALF WRONG and would have DRAINED THE CITY. Below the
  waterline those walls are STRUCTURAL: the canal is cut to -30 m while the rings only reach -10 m, so
  it is a trench slicing BENEATH the city base. Strip them and the canal empties into the void.
  Correct fix: walls run the WHOLE length BELOW sea level (containment); ABOVE sea level they exist
  ONLY where the canal cuts through land (quays).

### INVARIANT 3 (design, HARD RULE) — idempotent re-runs fix CHANGED geometry, NOT REMOVED geometry
  Stale blocks persist. If a design change DELETES something, the command stream must explicitly CLEAR
  it -- a re-run alone will not. (Here: the open-cut air box is widened to cz±(w+1) so it also erases
  the old above-water quay walls.) This is the flip side of INVARIANT 1 and just as important.

- METHOD NOTE: three of my four wrong theories this session came from reasoning about the build instead
  of looking at it. Watching the client + one F3 reading located both bugs in minutes. LOOK FIRST.

## [design] 2026-07-12 — the city: procedural PLACEMENT + handcrafted GEOMETRY (kit of parts)

- DIAGNOSIS of "blocky rough cut": that is procgen's CEILING, not a polish problem. Procedural
  generation gave us correct MASS at 5 km; it cannot give DETAIL, because detail is authored, not
  computed. The land rings are lawns. Fix = a different technique, reusing the schematic engine.
- schem.py: shared Sponge-v2 writer extracted (stdlib only), with the top-level `Offset` fix baked in.
  temple_gen.py should be refactored onto it (dedupe) when convenient.
- city_gen.py: hand-authored parametric building kit (townhouse, courtyard house, shop row, shrine,
  tower -- real walls, doorways, windows, courtyards, parapets, flat roofs) + a layout pass that lays
  ring roads and radial streets across a land ring and stamps buildings into the plots, each rotated
  to face its street. Emits ONE angular WEDGE per .schem (the rings are far too big for one schematic).
- Keeps clear of: the rock-cut docks (inner band), the circuit wall (outer edge), the four cardinal
  passages/bridges, and the +X grand canal corridor.
- PASTE WITH `-a`. The schem holds ONLY solid blocks -- doorways/windows/interiors are cells we simply
  never set, so the air above the grass shows through. Nothing is carved, nothing overwrites terrain.
- DETERMINISM (INVARIANT 1): layout is seeded from (ring, sector), NEVER the clock. A re-run must
  reproduce the same city block-for-block or the build stops being idempotent and a mid-run restart
  would corrupt it. This is a real constraint on procedural content, not a nicety.
- HANDOFF to [exec]: (1) regenerate + re-run the core with the canal fixes; (2) then ONE wedge:
      python3 city_gen.py --ring 1 --sectors 32 --sector 0 --out city_r1_s00.schem
  paste it, and we LOOK at it before committing to all 64 wedges.

## [design] 2026-07-12 — WHIRLED SITE: cold Atlantis confirmed; vmodel.py extracted; terrain-clear needed

- SITE ([exec], via mcbiome.py): whirled (43500, 21000), northern archipelago. Canal axis due EAST to a
  jagged_peaks massif ~2,084 b out = causeway terminus. Cold: taiga, snowy beaches, frozen peaks.
- COLD AESTHETIC: **YES** -- and it is MORE faithful, not a compromise. Plato puts Atlantis BEYOND the
  Pillars of Heracles, i.e. the Atlantic, not the Mediterranean. Our palette already suits it:
  calcite/white-terracotta city + red terracotta roofs + copper/gold, against black water, pine and
  snow. Stronger image than the expected white-city-on-blue-sea.
  PLUS: //setbiome a temperate biome INSIDE the ring footprint so the city never accumulates snow and
  stays warm-toned, while the archipelago around it stays snowy. "Precise city, natural frame" --
  exactly the idea [exec] was testing with the windswept/meadow wedges. The biome tool earns its keep.
- vmodel.py ADDED: single source of truth for the vertical model + radii. All three generators
  (atlantis_cmds, temple_gen, city_gen) were DUPLICATING the vertical math -- a sea-level rebase would
  have meant three edits and one missed edit buries the temple. ANCHOR IS SEA LEVEL now:
    scratchpad SEA=-30 ; whirled SEA=63.  Everything else hangs off it.
  TODO (design): wire all three generators onto vmodel. DO NOT build in whirled until this is done --
  a Y-datum mismatch would put the temple underground.
- NEW REQUIREMENT for a REAL world (~54% of the footprint is existing island): a TERRAIN-CLEAR pass.
  In the void we placed into air; in whirled we must ERASE what nature put there -- trees, hills,
  peaks standing above the design surface. vmodel.clear_top provides the ceiling. Cost: block count
  rises a lot (clearing ~90 layers over 19.6M columns), but SAVE cost is unchanged (same ~76k chunks),
  so the Watchdog picture is the same. Build time goes up, not crash risk.
- SEQUENCING: do NOT abandon scratchpad. Finish validating there (canal fixes + one city wedge) -- it
  is the cheap test bed. Whirled prep (vmodel wiring, terrain-clear, biome plan) runs in PARALLEL.

## [exec->design] 2026-07-12 — ROOT CAUSE, finally: SYNCHRONOUS WORLDGEN on the main thread

- [exec] caught it: the main thread hung 290s inside vanilla worldgen (Perlin/density functions).
  FAWE touching an UNGENERATED chunk makes Paper generate it SYNCHRONOUSLY on the main thread, and a
  big batch blows the Watchdog. This was never primarily a save problem.
- RETROACTIVE: hours ago we measured "first op at the virgin frontier = 240s" and filed it as a TIMING
  cost. It was the killer all along. We spent the session optimizing the thing we could see (saves,
  chunk counts, flush granularity) while the actual cause sat in a line we had already written down.

### INVARIANT 4 (HARD RULE) — NEVER let FAWE touch an ungenerated chunk
  Pre-generate the FULL footprint with Chunky, VERIFY coverage, and only then edit. Non-negotiable at
  whirled: ~76k chunks pregenned before a single block is placed, and 54% of that footprint is real
  island so the carve WILL reach for edge chunks. Also freeze BlueMap during builds -- a resuming
  render crawling to the ungenerated fringe is the same trigger.

## [design] 2026-07-12 — IN-GAME REVIEW of both city districts (Cowork watching, Rick flying)

- VERDICT: RADIAL WINS, decisively. Rectilinear = scattered huts on a lawn (far too sparse, plots way
  oversized). Radial = a packed urban fabric of curved terraces, round towers, domes. It reads as a
  CITY. Round buildings also dissolve the skew bug outright -- a circle has no orientation.
- FIX 1 (bug): terraces were laid across the FULL angular span and the roads painted afterwards at
  ground level only -- so buildings SQUATTED ON THE CROSS STREETS (road drawn, walls still standing).
  Now: radial streets computed FIRST, terraces skip units that straddle one -- EXCEPT ~1 in 7, which
  OVERBUILDS the lane with an ARCHWAY through it. Rick's call, and right: a city that occasionally
  vaults a building over a lane reads better than a perfect grid.
- FIX 2 (variety): wall material was picked PER CELL, so every dwelling was a random speckle of the
  same three whites -- which is exactly why the street read flat. Now ONE wall + ONE roof material
  PER HOUSE. Coherent dwellings, varied street, zero new palette blocks.
- FIX 3 (canal, Rick caught my rationalisation): I had run quay walls UNDERWATER the whole length,
  arguing they were structural. Absurd on inspection. A CANAL IS A CUT THROUGH GROUND -- the fix is
  to give it ground: an EMBANKMENT from canal floor up to ring floor, channel dug out of it, earth
  holds the water, no underwater walls anywhere. Stale stubs explicitly erased (INVARIANT 3). Past
  the outer water ring the embankment rises to sea level as a harbour mole.
- ACCEPTED AS-IS: some "twisting" of roofs/walls where arcs rasterize. Rick: hand-edit, not proc-edit.
  Correct call -- procgen's ceiling again; this is exactly the seam where authored work belongs.

## [design] 2026-07-12 — radial v2 APPROVED by Rick; city was clobbering the circuit wall (fixed)

- Rick on v2: "MUCH better. Streets lay out nicely, the arches are a nice touch, the single-coloured
  houses look much better and more diverse. Feels like a large city, not a congested ghetto."
  PATTERN IS SETTLED: curved terraces + round towers + tholoi, one material per house, cross streets
  clear with ~1-in-7 archway overbuilds.
- BUG (Rick): the city CLOBBERED THE CIRCUIT WALL on the outer side. Two causes:
    1. the road band ran to r1 + road_w, which lands ON the wall's inner face and repaints a course
       of it at street level;
    2. towers (radius 5) on the outermost ring road could reach it.
- FIX, and the gap is now a FEATURE not just a setback: real walled cities keep a clear strip inside
  the ramparts (the Roman POMERIUM) with a road along it. So:
    r_nobuild  = r_out - wall_t - 2   HARD clamp; nothing may ever cross it (roads included)
    r_wallroad = r_out - wall_t - 6   the pomerium -- a wall-walk ring road inside the wall
    r1         = r_out - wall_t - 12  buildings stop here
  Towers additionally bounded clear of BOTH the wall and the rock-cut docks.

## [design] 2026-07-12 — THE MARKET QUARTER on the pomerium (Rick's idea, and historically exact)

- Rick: "the inside road (pomerium) would be a great place for market stalls and shops -- makes sense
  from a traffic and human perspective." Correct on both counts, and it is a real historical pattern:
  markets go where traffic concentrates AND where there is open ground, and the pomerium is both. It
  is also the strip every GATE empties into (canal + bridges pierce the wall here), so anyone entering
  the city walks straight into it. Shops built against the inside of a city wall = the souk, the
  wall-market, the medieval lean-to. Oldest urban pattern there is.
- IT ALSO FIXES SOMETHING I HADN'T VOICED: the city has NO COLOUR. White housing is right and
  disciplined but bloodless. **All the colour now lives in the bazaar** -- striped awnings (orange /
  red / yellow / brown terracotta), copper wares (Atlantis was famed for metal), produce. Dwellings
  stay white; the life is in the market. This is a design PRINCIPLE, not just an addition.
- Pomerium widened into a market quarter, outward from the housing:
    r1          terraced housing stops
    r_stalls    freestanding canopy stalls (posts + awning + counter + wares)
    r_wallroad  the pomerium road itself
    r_shops_in  shop fronts: open, counters, awnings projecting over the street
    r_shops_out shop backs, against the rampart
    r_nobuild   HARD limit -- nothing may ever cross it
  ~12% of shop bays left as gaps (alleys / stairs up to the wall); stalls ~55% density so you can walk.

## [design] 2026-07-12 — THE WATERFRONT (dock_gen.py): the city finally meets its sea

- THE HOLE: Atlantis is a MARITIME city that was turning its back on the water. Three rings of sea,
  and no quay, no steps, no mooring, no ships -- you could walk off a land ring and fall in. Plato is
  emphatic about the opposite ("the docks were full of triremes and naval stores"; the harbours kept
  up "a multitudinous sound of human voices, and din and clatter of all sorts night and day").
- STRUCTURAL BUG FOUND: the dock gallery was cut **12 m deep**. A trireme is ~20 m long -- the ships
  did not fit in their own docks. Now 28 m (vmodel.dock_depth), which berths a hull plus working room.
- MATERIALS (Rick + Plato): PRISMARINE as the FACING -- the only stone family that reads sea-worn; it
  belongs to the water as the tri-colour stone belongs to the land. The mass and ROOFS stay NATIVE
  ROCK (calcite/granite/blackstone) because Plato is explicit: "roofs formed out of the native rock."
  Dark oak decking for piers; WAXED COPPER for bollards, mooring rings, lamp brackets (orichalcum).
- LIGHT (Rick asked for something that fits): SEA LANTERNS set into the quay face BELOW the waterline
  -- they are literally made of prismarine, so the water itself glows cold blue-green. HANGING
  LANTERNS on chains under the rock roof for warm working light. Cold sea-light in the water, warm
  fire-light under the stone. Also functional: an unlit cavern this size is a mob farm.
- FORM: piers divide the hollow gallery into individual BERTHS ("double docks" = ships in ranks, not
  one long trench), each decked in dark oak at the waterline so you can walk a moored hull. Quay wall,
  wharf paving on the dock roof, bollards + mooring chains, and NAVAL STORES (warehouses) set back
  from the wharf -- industrial character against the white housing and the coloured market.
- ARCHITECTURE: dock_gen.py is purely ADDITIVE (`-a` paste). A `-a` paste CANNOT carve, so the
  HOLLOWING stays in atlantis_cmds (docks phase) and the schematic builds piers/facing/decks/lights/
  stores INTO that void. Same bulk-by-command, detail-by-schematic split as everything else.
- COLOUR PRINCIPLE holds: white housing / coloured market / and now the docks read industrial --
  prismarine, timber and copper. Each quarter has its own register.

## [design] 2026-07-12 — docks REBUILT to the excavated ship sheds at ZEA. I nearly fixed the wrong thing.

- Rick flew the docks: "not sure how much of this you intended to be underwater... it landed a little
  low." MEASURED (F3, standing on the pier deck): Y=-28, deck at -29, water tops at -30. The PASTE IS
  CORRECT. The design was wrong.
- I had a theory (freeboard too small, raise the whole vertical model from 8 m to 14 m) and was one
  command from committing it. Rick sent the Trireme article instead. THE ARCHAEOLOGY KILLED MY THEORY:

  EXCAVATED SHIP SHEDS (neosoikoi) at ZEA -- the war harbour of Athens, i.e. the literal building
  we are making (Dragatsis/Doerpfeld; corroborated by Vitruvius):
      shed ~40 m LONG, just 6 m WIDE, interior height 4.026 m
      trireme just under 37 m long, hull 2.15 m above water, DRAUGHT ~1 m

  I had it almost exactly INVERTED: I built 28 long x 16 wide x 6 high. Real sheds are LONG, NARROW
  and LOW. That is why it read as a flooded cellar -- it was a ROOM when it should be a SLOT.

- THE DRAUGHT IS THE KEY. A trireme draws ONE METRE. These ships were not moored floating in deep
  water -- they were HAULED OUT up a sloping slipway and stored DRY. That is WHY the sheds are narrow:
  one hull each, dragged up stern-first, in ranks. The 4 m ceiling is not cramped, it is CORRECT.
- AND IT VINDICATES THE 8 m FREEBOARD. My "raise the land to 14 m" fix would have been wrong AND
  expensive. The vertical model is fine; the berth proportions were the fault.
- REBUILT: vmodel gains shed_width(6) / shed_pier(3) / slip_mouth(sea-2) / slip_head(sea+2) /
  shed_roof(sea+6); dock_depth 28 -> 44 (40 m shed + back wall). dock_gen now builds a SLOPING
  SLIPWAY: submerged at the sea end so the hull floats in, rising to dry ground at the head where the
  ship is drawn up. Hauling bollard at the head, mooring chain at the mouth.
- LESSON (again, and I keep having to relearn it): I have now been wrong about this build four times
  by reasoning instead of measuring, and every single correction came from LOOKING or from a SOURCE.
  The F3 reading killed the paste theory; the excavation killed the freeboard theory.

## [design] 2026-07-12 — OVER-CORRECTED: it's a TRADING port, not an arsenal (Rick)

- Rick: "These are trading docks, not war machine slots below the rim. We need TWO things -- narrow
  trireme slots in some parts, but the MAJORITY are working docks: Phoenician traders coming and
  going, unloading cargo."  CORRECT, and it is a PROGRAM-level error, not a detail one. I was handed
  one beautiful piece of archaeology (Zea) and turned the WHOLE waterfront into a navy base.
- PLATO AGREES WITH RICK, and I had already quoted the line: the harbours were "full of vessels and
  MERCHANTS coming from all parts... a multitudinous sound of human voices, and DIN AND CLATTER of all
  sorts night and day" (§E). The triremes and naval stores are there too (§D) -- but the NOISE is
  CARGO. I built the quiet half and forgot the loud one.
- THE SHIP TYPES DEMAND DIFFERENT BERTHS, and that IS the design:
    TRIREME     -- 37 x 6 m, draught 1 m. HAULED OUT, stored DRY in a roofed shed. Cannot moor.
    MERCHANTMAN -- Phoenician "round ship": beamy, deep-drafted, sail. STAYS AFLOAT, moors ALONGSIDE,
                   gets UNLOADED. You cannot berth these two in the same structure.
- REBUILT dock_gen as TWO segment types (NAVAL_FRACTION = 0.30):
    NAVAL   (minority, clustered) -- the neosoikoi as built. The arsenal.
    TRADING (majority) -- a LOW OPEN QUAY built OUT into the water at ~2 m above the waterline
            (you cannot unload a ship onto a wharf 8 m above its deck). Merchantmen moor alongside;
            derrick cranes, gangplanks, cargo stacks. AND the rock gallery behind becomes what it
            should always have been: VAULTED BONDED WAREHOUSES with an open arcade onto the quay.
            Cargo comes off the ship, across the quay, into the vaults. THE CAVE IS THE STORAGE,
            NOT THE BERTH. That is the insight that makes the whole waterfront click.
    Plus steps from the wharf up to the city (the land is 8 m above the water -- there was no way up).
- trireme:park added -- a STATIC trireme display (no boat/physics) for ships drawn up in the sheds,
  and as a platform to climb on. Inherits the player's yaw so it lies along the shed.
- STILL WANTED: a MERCHANTMAN model (beamy round ship) to moor at the trading wharves. The trireme
  model is a warship and will look wrong tied up at a cargo quay.

## [exec] 2026-07-12 — Temple of Poseidon pasted on citadel (schematic engine) + Offset fix

- temple_gen.py DATA_VERSION=4790 CONFIRMED correct (version.json world_version=4790, level.dat=4790;
  pack formats moved to 84/101 but the world DataVersion did not).
- CALIBRATION FIX: temple_gen wrote only Metadata WEOffset -> `//paste -o` landed the temple at the
  NEGATED position (10016,51,-9992) instead of (-10016,-51,9992). FAWE reads WEOffset as origin->min
  (negated for -o). Added the top-level Sponge `Offset` int-array = absolute min corner (the POC's
  proven approach); FAWE's -o then places the min corner AT Offset. Re-pasted -> lands on the citadel.
  (Same deterministic path as the original POC; the POC worked because it wrote the top-level Offset.)
- Verified headlessly on scratchpad citadel (-10000/10000): silver pylon iron_block @ (-9986,-46);
  gold pinnacle cap @ -44; orichalcum waxed_cut_copper columns (hypostyle); gold_block sanctuary (-X);
  smooth_quartz walls; centre redstone marker runs up through (harmless). 33x10x17, 2206 blocks.
- At S=30 it's a doll's house as expected; the payoff is S=185 (30-block nave, looming pylon).

---

## [design] 2026-07-12 — THE MERCHANTMAN + a scale bug in park.mcfunction (ships are now a family)

Rick: "go for a merchant ship. Also, you might get some inspiration from Piraeus, the greek port."

PIRAEUS SETTLES THE LAYOUT ARGUMENT. Piraeus is not one harbour, it is THREE, and they were
functionally segregated: **Kantharos** was the commercial harbour (the *emporion*, with the deigma
sample-market and the grain stores); **Zea** and **Mounichia** were the naval basins, and Zea is
where the 196 ship sheds we already used for the neosoikoi were excavated. Navy and trade sat in
PHYSICALLY SEPARATE BASINS. So dock_gen's naval segments should be CLUSTERED into an arsenal
quarter, not sprinkled at 30% around the whole rim. (Not yet changed in dock_gen.py — see TODO.)

THE SHIP ITSELF — anchored on the KYRENIA WRECK (4th c. BC, sank c. 294 BC; the best-preserved
Greek merchant hull we have; ~381 amphorae recorded aboard, mostly Rhodian — wine, oil, almonds):

| | trireme | merchantman (Kyrenia) |
|---|---|---|
| length | ~37 m | **14 m** |
| beam | 6 m | **4.4 m** |
| ratio | **6.2 : 1** | **3.2 : 1** |

That ratio IS the animal. A trireme is a needle; a merchantman is a tub. The visual tells, all now
in the model: deep round belly, **NO RAM** (the single clearest trader-vs-warship cue), one mast
with a big square sail, curved sternpost, **quarter-rudders** not a stern rudder, cargo on deck.

NEW: resourcepack/assets/trireme/models/item/merchantman.json (+ items/merchantman.json).
  Model is 1.8125 blocks long x 0.625 beam = 2.9:1 in-model, so the tub ratio survives the render.

BUG FOUND AND FIXED — park.mcfunction was parking triremes at scale 4.0 = a **12 m** ship. We then
built **40 m** ship sheds off the Zea excavation. We would have been parking a toy in a boathouse.
The trireme model is 3.0 blocks long, so TRUE SCALE is 37/3.0 = 12.3; park now uses **12.0** ->
36 m long, 4.5 m beam. That the model's own beam then lands inside the excavated 6 m shed with
~0.75 m clearance either side is independent confirmation the hull proportions are right.
LESSON (again): the archaeology is load-bearing. Every number we took from a source has held; every
number I eyeballed has had to be redone.

DATAPACK — ships are now a FAMILY, not a one-off. Generic tags `ship_boat`/`ship_disp` (rideable),
`ship_parked` (dry, in a shed), `ship_moored` (afloat, alongside):
  trireme:summon      rideable trireme      (scale 4.0, unchanged; now also carries the generic tags)
  trireme:merchant    rideable merchantman  (scale **3.0**, NOT 4.0 — see below)
  trireme:park        static trireme, dry in a shed   (scale 12.0 = 36 m)
  trireme:moor        static Kyrenia coaster alongside (scale 7.5  = 13.6 m x 4.7 m)
  trireme:moor_large  static deep-sea trader alongside (scale 14.0 = 25.4 m x 8.8 m)
  trireme:moor_at     MACRO: {scale:"..",sink:".."} — tune without editing files
  trireme:uninstall   clears every ship of every type
- tick.mcfunction is now ONE line keyed on the generic tags, so it covers all rideables and any
  future hull. summon.mcfunction had to gain those tags or the trireme would have silently stopped
  turning — the kind of break a "just add a file" change hides.
- Static ships are deliberately NOT ticked: no vehicle, rotation set once at summon.
- WHY merchant scale 3.0 and not 4.0: rendering both hulls at 4.0 would make the trader 60% of the
  warship's length when the real ratio is 38%. 3.0 gives a 5.4-block coaster that reads correctly
  next to a 12-block trireme.
- moor_large exists because Kyrenia is the best-PRESERVED merchantman, not the biggest — she was a
  coaster. Mixed tonnage makes the wharf read as a working port, not a car park of identical hulls.

TUNABLE, and it is the one number worth eyeballing in-game: the `sink` on the moored hulls (-4.5 /
-6.0). It assumes the quay deck sits 2 m above the sea (dock_gen: quay_y = sl + m2b(2)) and the
hull wants ~1.3 m of draught. If she rides high and shows keel, sink further; if the deck is awash,
raise. Use trireme:moor_at to iterate without a repack.

USAGE (matters, and is not obvious): to moor, stand on the quay deck and look **ALONG** the quay,
not out to sea — the hull inherits your yaw, so looking seaward berths her bow-on into the stone.
To park, stand at the head of the slipway and face down the shed toward the water.

TODO for exec: needs a resourcepack reload (the new model + item definition) and a `/reload` for
the datapack. Then: /function trireme:moor on a trading quay, /function trireme:park in a shed.

TODO for design (me): cluster the naval segments into a Zea-style arsenal quarter instead of
NAVAL_FRACTION=0.30 scattered around the rim; Piraeus says they were separate basins.

---

## [design] 2026-07-12 — THE BIG ONE: canal 6x too narrow, rings 3x too short, merchants in the
## wrong rings, and the whole city zoned wrong. Rick found all four. FULL REBUILD next run.

Rick, flying the S=185 core: "the land rings feel VERY cramped... having water passages BEHIND the
quay with no access is odd... at scale, how WIDE should the grand canal be? Given the scale and
grandeur of the temple, this feels sandwiched in."  Then, later: "each of the rings has a unique set
and style of buildings (residential, administrative, military, core) and probably needs unique
design."  Every one of these was right. New docs: **HARBOUR_SPEC.md**, **RING_SPEC.md**. vmodel.py
rewritten (v2) and is now the enforcing source of truth.

ROOT CAUSE OF ALL OF IT: we took Plato's PLAN dimensions literally and then EYEBALLED the third
dimension and the PROGRAMME. Radii: sourced. Everything else: invented.

### 1. THE CANAL WAS SIX TIMES TOO NARROW (§B, literal)
"a canal of THREE HUNDRED FEET IN WIDTH and ONE HUNDRED FEET IN DEPTH." A stade is 600 ft, so
300 ft = HALF A STADE = 92 m. We built 15 m. The canal was DEEPER (31 m) THAN IT WAS WIDE.
HOW IT SURVIVED, and this is the lesson: `canal_w = 7` was a HARDCODED HALF-WIDTH, the only
dimension in the build not passing through m2b(). At S=30 -- THE SCALE WE VALIDATED THE ENGINE AT --
ft2b(300) = 15, i.e. half-width 7. IT WAS CORRECT. The magic number was calibrated at the scale
where it happened to be right, then frozen while S went to 185.
  ==> vmodel gains ft2b(). Plato's foot-measures now survive AS FEET.
  ==> AND THE COUPLING THAT HID IT: `tun_hw = canal_w - 1`. ONE KNOB DOING TWO JOBS. Fixing the canal
      would have blown the trireme tunnels out to 91 m. Now independent (§B sizes them differently:
      the canal takes "the LARGEST VESSELS", the tunnels take "a SINGLE TRIREME").
  ==> ALSO MISSED IN §B, found on re-fetch: "leaving an opening sufficient to enable the LARGEST
      VESSELS to find ingress." Independent confirmation of the 92 m figure.

### 2. THE BANKS WERE A CURB (§B)
y_land = sea+8, headroom = sea+6 -> A TWO-METRE ROCK ROOF over a ship channel, carrying a road and a
city. §B: "they covered over the channels... FOR THE BANKS WERE RAISED CONSIDERABLY ABOVE THE WATER."
It also silently foreclosed §B's "they HOLLOWED OUT DOUBLE DOCKS, having roofs formed out of the
native rock" -- YOU CANNOT QUARRY A DOCK INTO AN 8 m CLIFF.
  ==> Rings STEP UP toward the centre (Rick chose "masts up"):
        L2 sea+24 (10 m rock roof) | L1 sea+36 (22 m) | citadel sea+55 | belt sea+12
        headroom 14 m -> a merchantman passes the tunnels WITH ITS MAST UP
        circuit walls now stand 8 m above THEIR OWN ring (they would otherwise have been BURIED)
        temple pinnacle lands ~100 m above the sea
  ==> vmodel now ASSERTS roof thickness at construction. The 2 m roof shipped because NOTHING WAS
      CHECKING. A ring too short for its headroom now raises at import.
  ==> "DOUBLE DOCKS": Rick reads it HORIZONTALLY (two ships nose-to-tail), not as stacked levels --
      also the standard reading of double neosoikoi. dock_depth 44 -> 88 m.

### 3. THE MERCHANTS WERE IN THE WRONG RINGS -- and DEFENCE is what proved it
Rick, reasoning from FORTIFICATION, not from Plato: "it doesn't make sense to put docks with access
up to the city in the OUTER walls - a massive vulnerability... merchant cargo would want protection
from raiders, pirates, and the sea itself."
The text says so twice, and I had QUOTED BOTH LINES WITHOUT READING THEM:
  §B: the canal "they carried through to THE OUTERMOST ZONE... WHICH BECAME A HARBOUR"
  §E: "THE CANAL AND THE LARGEST OF THE HARBOURS were full of vessels and merchants... din and
      clatter of all sorts night and day"
And the clincher:
  §B: the inter-ring passages leave "room for a SINGLE TRIREME to pass out of one zone into another."
  YOU CANNOT RUN A CARGO ECONOMY THROUGH A ONE-SHIP-AT-A-TIME ROOFED TUNNEL. IT IS A NAVAL SALLY PORT.
  ==> W3 (outermost, 3 stades, brass wall, fed by the 92 m canal) = THE EMPORION. Trading quays.
  ==> W1 + W2 (interior, single-trireme tunnels only)             = THE ARSENAL. Neosoikoi.
  ==> Rick's "dead water behind the quay" WAS NEVER WRONG. It is a 44 m flooded slipway gallery: the
      ARSENAL, IN THE RIGHT PLACE, WITH THE WRONG TENANT. dock_gen floored it over because it was
      building a trading port there. Move the trade out; the navy moves in.
  ==> Cargo goes on W3's OUTER shore (the city side), backed by 50 stades of dense city -- NOT on an
      exposed outer wall. Rick's threat model, verbatim. Inner shore (L2's cliff) = official side:
      customs, the deigma, grand stairs, brass wall on the skyline.
  ==> This is Piraeus (Kantharos commercial / Zea + Mounichia naval), reached from Plato + a threat
      model rather than imposed from the archaeology.

### 4. EVERY RING IS A DIFFERENT CITY (Rick) -- and §D SPELLS IT OUT
Our own PLATO_SOURCE §D was TRUNCATED WITH AN ELLIPSIS, and the elided text was the most important
zoning passage in the dialogue. Restored. It says:
  "...in the centre of THE LARGER OF THE TWO there was set apart a RACE-COURSE OF A STADIUM IN WIDTH,
   and in length allowed to EXTEND ALL ROUND THE ISLAND, for horses to race in. Also there were
   GUARDHOUSES at intervals for the guards, THE MORE TRUSTED OF WHOM were appointed to keep watch in
   THE LESSER ZONE, WHICH WAS NEARER THE ACROPOLIS, while THE MOST TRUSTED OF ALL had houses given
   them WITHIN THE CITADEL, near the persons of the kings."
  ==> THE RINGS ARE RANKS. Least-trusted guard on L2 -> more-trusted on L1 -> most-trusted in the
      citadel. The concentric plan is a SECURITY GRADIENT. Same logic Rick used on the docks.
  ==> THE LAND RINGS ARE NOT RESIDENTIAL. §E puts the dense housing in the BELT.
      city_radial.py IS NOT WRONG -- IT IS AIMED AT THE WRONG ZONE. It is the BELT generator.
  ==> THE RACECOURSE IS A HARD CONSTRAINT: 1 stade wide, down the CENTRE of L2 (r 8.5->9.5 stades)
      = a 185 m track with a 10.5 km lap. It consumes the middle third of L2 and dictates the ring.
  ==> Four characters: CITADEL monumental/sacred | L1 ORDERED (barracks in ranks, the most regular
      geometry in the build) | L2 OPEN (the racecourse void, stables, horse country) | BELT DENSE
      (city_radial). L2's openness across the harbour from the belt's density is the strongest urban
      move available and we currently have NEITHER.
  ==> Free win: city_radial's pomerium market was designed to back onto the circuit wall. The belt's
      INNER edge IS the emporion shore -- so the market lands exactly where the ships unload. The
      pomerium market becomes the QUAYSIDE market, which is what an emporion IS.

### 5. AND ONE FOR THE PALETTE (§B, missed on the first pass)
"Some of their buildings were simple, but in others they put together DIFFERENT STONES, VARYING THE
COLOUR TO PLEASE THE EYE, and to be a natural source of delight."
Rick's "use all the colors of the minecraft stone... interesting, but consistent" IS IN THE TEXT.

### DECISION: FULL REBUILD (Rick)
"the next run should be a complete rebuild, just to clear the remains of the intermediate placing
and cuts."  CORRECT, and it RETIRES A CLASS OF RISK: every fix above would otherwise have to fight
INVARIANT 3 (idempotent re-runs fix CHANGED geometry, NOT REMOVED geometry) -- buried wall tops, the
15 m canal's banks, the floored-over gallery, the city on the wrong rings. A `//set air` wipe then
one clean stream and INVARIANT 3 STOPS APPLYING. Cheaper to reason about than any patch sequence.

### THE META-PATTERN, now undeniable
EVERY correction in this project has come from LOOKING (Rick flying it + computer-use/F3) or from a
SOURCE (Plato's text, the Zea excavation, the Kyrenia wreck). NOT ONE has come from me reasoning.
The numbers I took from a source have ALL held. The numbers I eyeballed have ALL had to be redone.
Corollary discovered today: a magic number that PASSES ITS TEST AT THE VALIDATION SCALE is the most
dangerous kind, because the test certifies it. Derive, don't calibrate.

### STATE / NEXT
- vmodel.py v2: DONE (ft2b, stepped rings, canal/tunnel decoupled, roof assertion, arsenal+emporion).
- HARBOUR_SPEC.md, RING_SPEC.md, PLATO_SOURCE §D+§B restored: DONE.
- NOT YET DONE (the code): atlantis_cmds.py (canal width, stepped vertical, wall heights, carve
  locations, belt surface); dock_gen.py (invert: trading -> W3 both shores, naval -> L1/L2 inner
  faces, 88 m double sheds); city_radial.py re-aim to the belt; ring_l1_gen.py; ring_l2_gen.py
  (racecourse first -- it dictates the ring).
- COST: rings roughly double (~+120M blocks at S=185); canal ~6x volume. Both are //generate -r
  annulus/box work (the cheap path) but the stream needs a LOWER --phase-every than the core run.
- NOTE FOR EXEC: bash could not mount the repo from Cowork's sandbox this session (UNC), so
  `python3 vmodel.py` has NOT been run. First thing CC should do: run it and eyeball the dump.
