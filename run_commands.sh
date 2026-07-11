#!/usr/bin/env bash
# Run from WSL. Pipes a FAWE command script through the `mc` console FIFO, waiting for
# completion after each heavy op, then probes the centre marker.
# Reuses the exact headless path the POC proved -- payload is commands, not a .schem.
#
# Fixes folded in from the 30-scale validation:
#  - //generate reports "N blocks have been created", NOT "Operation completed"
#    (only //set/#//paste print "Operation completed") -> wait pattern matches BOTH.
#  - marker probe needs `execute in <dimension>` or it false-negatives -> DIM threaded.
set -euo pipefail

SSH_ALIAS="${SSH_ALIAS:-ptx-minecraft}"
SRV="${SRV:-/home/papercraft/papermc}"
WORLD="${WORLD:-scratchpad}"
CMDFILE="${CMDFILE:-atlantis_30.commands}"
# centre-marker probe (generator centre column; y_island+1 = -52)
PX="${PX:--10000}"; PY="${PY:--52}"; PZ="${PZ:-10000}"

[ -f "$CMDFILE" ] || { echo "no command file: $CMDFILE (run: python3 atlantis_cmds.py --scale 30 --out $CMDFILE)"; exit 1; }

echo ">> shipping ${CMDFILE} -> ${SSH_ALIAS}:/tmp/atlantis.commands"
scp "$CMDFILE" "${SSH_ALIAS}:/tmp/atlantis.commands"

ssh "${SSH_ALIAS}" SRV="$SRV" WORLD="$WORLD" PX="$PX" PY="$PY" PZ="$PZ" bash -s <<'REMOTE'
set -uo pipefail
LOG="$SRV/logs/latest.log"
DIM="minecraft:${WORLD}"
DONE='Operation completed|blocks have been created'   # //set AND //generate
MAXWAIT="${MAXWAIT:-600}"                              # safety net; a real stall pauses+flags

send(){ printf '%s\n' "$1" > "$SRV/console.in"; }
mark(){ wc -l < "$LOG"; }

n=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  case "$line" in \#*) continue ;; esac
  n=$((n+1))
  case "$line" in
    *"//generate"*|*"//set"*|*"//paste"*)
      b=$(mark); send "$line"
      # FAWE gates large edits behind a "Use //confirm" prompt -- the op will NOT run until
      # acknowledged. Poll for completion; ack the confirm once if it appears; NEVER advance on
      # a stall (per ownership split: a timeout pauses and flags, it does not skip the op).
      confirmed=0; done_ok=0; t=0
      while [ "$t" -lt "$MAXWAIT" ]; do
        new=$(tail -n +$((b+1)) "$LOG")
        printf '%s' "$new" | grep -Eq "$DONE" && { done_ok=1; break; }
        if [ "$confirmed" = 0 ] && printf '%s' "$new" | grep -qi 'Use //confirm'; then
          send "//confirm"; confirmed=1
        fi
        sleep 1; t=$((t+1))
      done
      res=$(tail -n +$((b+1)) "$LOG" | grep -E "$DONE" | tail -1 | sed -E 's/^\[[^]]*\][^]]*\]: //')
      tag=""; [ "$confirmed" = 1 ] && tag=" (confirmed)"
      if [ "$done_ok" = 1 ]; then
        echo "[$n] ${line}  ->  ${res}${tag}"
      else
        echo "[$n] ${line}  ->  !! STALLED ${t}s (confirmed=$confirmed) -- PAUSING, not advancing"
        echo "   last server lines:"; tail -n +$((b+1)) "$LOG" | grep -viE 'Villages|Storage' | tail -4 | sed 's/^/     /'
        exit 2
      fi
      ;;
    *) send "$line"; sleep 0.3; echo "[$n] $line" ;;
  esac
done < /tmp/atlantis.commands

echo "== verify centre marker at $PX $PY $PZ in $DIM =="
# forceload the centre chunk so the vanilla probe can't false-negative on an unloaded chunk
send "execute in $DIM run forceload add $PX $PZ"; sleep 1.5
b=$(mark)
send "execute in $DIM if block $PX $PY $PZ minecraft:redstone_block run say ATLANTIS_MARKER_OK"
ok=0; t=0; while [ "$t" -lt 8 ]; do
  tail -n +$((b+1)) "$LOG" | grep -q "ATLANTIS_MARKER_OK" && { ok=1; break; }
  sleep 1; t=$((t+1))
done
[ "$ok" = 1 ] \
  && echo "PLACEMENT: marker present at ($PX,$PY,$PZ) -> ON TARGET" \
  || echo "PLACEMENT: marker NOT found -> report where the redstone column actually is"
send "execute in $DIM run forceload remove $PX $PZ" >/dev/null 2>&1 || true

send "//world" >/dev/null 2>&1 || true
REMOTE

echo ">> done. Fly to $PX ~ $PZ in ${WORLD} to eyeball."
echo ">> revert note: //generate + //set are separate undo steps -- a blind //undo won't unwind the"
echo ">>   whole build. For a full clear, //set air over the footprint bbox (as in the cleanup script)."
