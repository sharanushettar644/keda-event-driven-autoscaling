#!/usr/bin/env bash
# End-to-end autoscaling test (used by CI, runnable locally after kind-up.sh):
#   1. consumers start at 0
#   2. a burst of messages scales them out to several pods
#   3. every message is processed
#   4. consumers scale back to 0 once the queue is empty
set -euo pipefail
cd "$(dirname "$0")/.."

NS=keda-demo
MIN_PEAK=${MIN_PEAK:-3}
TIMELINE=${TIMELINE:-scaling-timeline.txt}

ready() { kubectl -n "$NS" get deploy consumer -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true; }
depth() {
  kubectl -n "$NS" exec deploy/rabbitmq -- rabbitmqctl -q list_queues name messages_ready messages_unacknowledged \
    | awk '$1=="jobs" {print $2+$3; f=1} END {if (!f) print 0}'
}
log() { printf "%-8s %-10s %-10s %s\n" "$(( $(date +%s) - START ))s" "$(depth)" "${1:-0}" "${2:-}" | tee -a "$TIMELINE"; }

START=$(date +%s)
printf "%-8s %-10s %-10s %s\n" "elapsed" "queue" "consumers" "event" | tee "$TIMELINE"

r=$(ready); [ "${r:-0}" -eq 0 ] || { echo "FAIL: expected 0 consumers before the test, found $r"; exit 1; }
log 0 "start: idle, scaled to zero"

bash scripts/load-test.sh >/dev/null
log "$(ready)" "producer finished publishing"

peak=0
deadline=$(( $(date +%s) + 240 ))
while :; do
  r=$(ready); r=${r:-0}; [ "$r" -gt "$peak" ] && peak=$r
  q=$(depth)
  log "$r"
  if [ "$q" -eq 0 ] && [ "$peak" -ge "$MIN_PEAK" ]; then break; fi
  [ "$(date +%s)" -lt "$deadline" ] || { echo "FAIL: queue=$q peak=$peak after 240s"; exit 1; }
  sleep 5
done
log "$(ready)" "queue drained (peak consumers: $peak)"

deadline=$(( $(date +%s) + 300 ))
while :; do
  r=$(ready); r=${r:-0}
  log "$r"
  [ "$r" -eq 0 ] && break
  [ "$(date +%s)" -lt "$deadline" ] || { echo "FAIL: consumers did not scale back to zero"; exit 1; }
  sleep 10
done
log 0 "scaled back to zero"

echo
echo "PASS: 0 -> $peak consumers -> 0, all messages processed in $(( $(date +%s) - START ))s"
