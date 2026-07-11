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
      t=0; while [ "$t" -lt 300 ]; do
        if tail -n +$((b+1)) "$LOG" | grep -Eq "$DONE"; then break; fi
        sleep 1; t=$((t+1))
      done
      res=$(tail -n +$((b+1)) "$LOG" | grep -E "$DONE" | tail -1 | sed -E 's/^\[[^]]*\][^]]*\]: //')
      echo "[$n] ${line}  ->  ${res:-<timeout ${t}s>}"
      ;;
    *) send "$line"; sleep 0.3; echo "[$n] $line" ;;
  esac
done < /tmp/atlantis.commands

echo "== verify centre marker at $PX $PY $PZ in $DIM =="
b=$(mark)
send "execute in $DIM if block $PX $PY $PZ minecraft:redstone_block run say ATLANTIS_MARKER_OK"
sleep 1
if tail -n +$((b+1)) "$LOG" | grep -qE "ATLANTIS_MARKER_OK|Test passed"; then
  echo "PLACEMENT: marker present at ($PX,$PY,$PZ) -> ON TARGET"
else
  echo "PLACEMENT: marker NOT found -> report where the redstone column actually is"
fi

send "//world" >/dev/null 2>&1 || true
REMOTE

echo ">> done. Fly to $PX ~ $PZ in ${WORLD} to eyeball."
echo ">> revert note: //generate + //set are separate undo steps -- a blind //undo won't unwind the"
echo ">>   whole build. For a full clear, //set air over the footprint bbox (as in the cleanup script)."
