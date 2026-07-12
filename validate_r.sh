#!/usr/bin/env bash
# Determine the coordinate frame of FAWE `//generate -r` on this build.
# WHY: real bbox-bounding tiling needs a WORLD-coordinate expression, because tiled sub-selections
# are NOT centred on the city, so the normalized `x^2+z^2<=1` circle trick breaks. Before S=185 we
# must know whether `-r` gives ABSOLUTE world coords or REGION-RELATIVE (min-corner) coords.
#
# METHOD: an OFF-CENTRE selection whose MIN corner sits exactly at a chosen world point C.
#   Test A (world-coord disc):  //generate -r stone (x-Cx)^2+(z-Cz)^2<=100   ; probe block at C
#   Test B (local-coord disc):  //generate -r stone  x^2+z^2<=100            ; probe block at C
# The disc is radius 10 centred on its origin. C is the selection's MIN CORNER, so:
#   - if A makes C=stone  -> `-r` is ABSOLUTE world coords   (origin at world 0)
#   - if B makes C=stone  -> `-r` is REGION-RELATIVE          (origin at selection min corner)
# Exactly one should hit. Clean, single-probe discriminator.
#
# Run from WSL. Uses the proven console FIFO + log-scrape path. Cleans up after itself.
set -uo pipefail

SSH_ALIAS="${SSH_ALIAS:-ptx-minecraft}"
SRV="${SRV:-/home/papercraft/papermc}"
WORLD="${WORLD:-scratchpad}"
# clear test area, well away from the Atlantis build; C = min corner = disc origin
CX="${CX:--9000}"; CY="${CY:--58}"; CZ="${CZ:-11000}"

ssh "${SSH_ALIAS}" SRV="$SRV" WORLD="$WORLD" CX="$CX" CY="$CY" CZ="$CZ" bash -s <<'REMOTE'
set -uo pipefail
LOG="$SRV/logs/latest.log"; DIM="minecraft:${WORLD}"
send(){ printf '%s\n' "$1" > "$SRV/console.in"; }
mark(){ wc -l < "$LOG"; }
wait_done(){ local b="$1" t=0; while [ "$t" -lt 30 ]; do
    tail -n +$((b+1)) "$LOG" | grep -Eq 'Operation completed|blocks have been created' && return 0
    tail -n +$((b+1)) "$LOG" | grep -qi 'Use //confirm' && send "//confirm"
    sleep 1; t=$((t+1)); done; }
probe(){ # $1 label -> echoes HIT/miss for stone at C
  local b; b=$(mark)
  send "execute in $DIM if block $CX $CY $CZ minecraft:stone run say ${1}_HIT"
  sleep 1
  if tail -n +$((b+1)) "$LOG" | grep -q "${1}_HIT"; then echo "$1: HIT (C is stone)"; else echo "$1: miss (C is air)"; fi
}

CX2=$((CX+40)); CZ2=$((CZ+40))    # selection extends +x,+z from the min corner C

send "//world $WORLD"; sleep 1
send "execute in $DIM run forceload add $CX $CZ $CX2 $CZ2"; sleep 2

echo "== Test A: world-coord disc centred at C ($CX,$CZ) =="
send "//pos1 $CX,$CY,$CZ"; send "//pos2 $CX2,$CY,$CZ2"; sleep 0.5
b=$(mark); send "//set air"; wait_done "$b"
b=$(mark); send "//generate -r minecraft:stone (x-($CX))^2+(z-($CZ))^2<=100"; wait_done "$b"
probe A

echo "== Test B: local-coord disc (origin at selection min corner) =="
send "//pos1 $CX,$CY,$CZ"; send "//pos2 $CX2,$CY,$CZ2"; sleep 0.5
b=$(mark); send "//set air"; wait_done "$b"
b=$(mark); send "//generate -r minecraft:stone x^2+z^2<=100"; wait_done "$b"
probe B

echo "== cleanup =="
send "//pos1 $CX,$CY,$CZ"; send "//pos2 $CX2,$CY,$CZ2"; b=$(mark); send "//set air"; wait_done "$b"
send "execute in $DIM run forceload remove $CX $CZ $CX2 $CZ2"; sleep 1
send "//world" >/dev/null 2>&1 || true

echo "== VERDICT =="
echo "  A HIT / B miss -> //generate -r = ABSOLUTE world coords  (tiling: use (x-Cx)^2+(z-Cz)^2 as-is)"
echo "  B HIT / A miss -> //generate -r = REGION-RELATIVE          (tiling: offset centre by each tile's min corner)"
echo "  (report which line hit)"
REMOTE
