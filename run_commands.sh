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
# FAWE runs edits ASYNCHRONOUSLY: a per-op "look for a completion line after my snapshot" window
# races the async flush and can miss/mis-attribute a completion. Instead we COUNT cumulative
# completion lines since run-start and wait until the count reaches the number of heavy ops
# dispatched. Immune to flush ordering; still pauses+flags on a genuine stall (count never catches up).
START=$(mark)
# donecount must survive latest.log ROTATION. At S=185 FAWE volume Paper's size-based policy
# rolls latest.log into a dated .gz mid-build; absolute line offsets then point past EOF of the
# fresh (short) file and the count silently reads 0 -> false stall. We BANK the exact completion
# count from each rotated-away file (re-read from its .gz) so the cumulative count spans rotations.
# Reading the .gz keeps it exact -- under-count would re-stall, over-count would skip ops.
BANK=0; SKIP=$START; LASTLEN=$START
donecount(){
  local cur; cur=$(mark)
  if [ "$cur" -lt "$LASTLEN" ]; then                       # latest.log rolled since last poll
    local gz; gz=$(ls -t "$SRV"/logs/*.log.gz 2>/dev/null | head -1)
    [ -n "$gz" ] && BANK=$((BANK + $(zcat "$gz" | tail -n +$((SKIP+1)) | grep -cE "$DONE") ))
    SKIP=0                                                  # subsequent front-file counted in full
  fi
  LASTLEN=$cur
  echo $((BANK + $(tail -n +$((SKIP+1)) "$LOG" | grep -cE "$DONE") ))
}

n=0; hcount=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  case "$line" in
    \#PHASE*)
      # Design emits #PHASE at each zone/feature boundary. Flush a save here so no single
      # save-all carries the whole delta (which would risk the 60s Watchdog kill at S=185).
      echo "[phase] $line -- flushing save"
      b=$(mark); send "save-all flush"
      t=0; while [ "$t" -lt 180 ]; do
        [ "$(mark)" -lt "$b" ] && b=0                       # log rolled during the save -> re-anchor
        tail -n +$((b+1)) "$LOG" | grep -q "Saved the game" && break; sleep 1; t=$((t+1))
      done
      echo "   saved (${t}s)"
      continue ;;
    \#*) continue ;;
  esac
  n=$((n+1))
  case "$line" in
    *"//generate"*|*"//set"*|*"//paste"*)
      hcount=$((hcount+1)); send "$line"
      # ack FAWE's large-edit //confirm gate once if it appears; wait until cumulative completions
      # catch up to hcount. NEVER advance on a stall (a timeout pauses and flags, never skips).
      confirmed=0; done_ok=0; t=0
      while [ "$t" -lt "$MAXWAIT" ]; do
        [ "$(donecount)" -ge "$hcount" ] && { done_ok=1; break; }
        if [ "$confirmed" = 0 ] && tail -n 80 "$LOG" | grep -qi 'Use //confirm'; then
          send "//confirm"; confirmed=1
        fi
        sleep 1; t=$((t+1))
      done
      res=$(tail -n +$((SKIP+1)) "$LOG" | grep -E "$DONE" | tail -1 | sed -E 's/^\[[^]]*\][^]]*\]: //')
      tag=""; [ "$confirmed" = 1 ] && tag=" (confirmed)"
      if [ "$done_ok" = 1 ]; then
        echo "[$n] ${line}  ->  ${res}${tag}"
      else
        echo "[$n] ${line}  ->  !! STALLED ${t}s @ op#${hcount} (have $(donecount) completions; confirmed=$confirmed) -- PAUSING"
        echo "   last server lines:"; tail -n 6 "$LOG" | grep -viE 'Villages|Storage' | sed 's/^/     /'
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
