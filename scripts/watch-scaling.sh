#!/usr/bin/env bash
# Prints queue depth next to consumer replicas every few seconds, so you can
# see scale-out from zero, the drain, and scale-in back to zero.
#   ./scripts/watch-scaling.sh            run until Ctrl-C
#   DURATION=300 ./scripts/watch-scaling.sh   stop after 300 seconds
set -uo pipefail

NS=keda-demo
INTERVAL=${INTERVAL:-5}
DURATION=${DURATION:-0}
start=$(date +%s)

queue_depth() {
  kubectl -n "$NS" exec deploy/rabbitmq -- \
    rabbitmqctl -q list_queues name messages_ready messages_unacknowledged 2>/dev/null \
    | awk '$1=="jobs" {print $2+$3; found=1} END {if (!found) print 0}'
}

printf "%-8s %-8s %-10s %-10s\n" "time" "elapsed" "queue" "consumers"
while :; do
  now=$(date +%s)
  replicas=$(kubectl -n "$NS" get deploy consumer -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
  printf "%-8s %-8s %-10s %-10s\n" "$(date +%H:%M:%S)" "$((now - start))s" "$(queue_depth)" "${replicas:-0}"
  if [ "$DURATION" -gt 0 ] && [ $((now - start)) -ge "$DURATION" ]; then break; fi
  sleep "$INTERVAL"
done
