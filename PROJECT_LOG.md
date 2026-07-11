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
