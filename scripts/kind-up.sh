#!/usr/bin/env bash
# Local cluster with everything needed for the demo:
# kind -> KEDA -> RabbitMQ + consumer (0 replicas) + ScaledObject.
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=${CLUSTER:-keda-demo}
KEDA_VERSION=${KEDA_VERSION:-}   # empty = latest chart

for bin in docker kind kubectl helm; do
  command -v "$bin" >/dev/null || { echo "Missing '$bin' - please install it first."; exit 1; }
done

if ! kind get clusters | grep -qx "$CLUSTER"; then
  echo ">> Creating kind cluster '$CLUSTER'"
  kind create cluster --name "$CLUSTER" --wait 120s
fi
kubectl config use-context "kind-$CLUSTER" >/dev/null

echo ">> Installing KEDA ${KEDA_VERSION:-(latest)}"
helm repo add kedacore https://kedacore.github.io/charts >/dev/null 2>&1 || true
helm repo update kedacore >/dev/null
helm upgrade --install keda kedacore/keda --namespace keda --create-namespace \
  ${KEDA_VERSION:+--version "$KEDA_VERSION"} --wait --timeout 5m

echo ">> Building the worker image and loading it into kind"
docker build -t keda-worker:local worker
kind load docker-image keda-worker:local --name "$CLUSTER"

echo ">> Deploying RabbitMQ, the consumer and the ScaledObject"
kubectl apply -k k8s/overlays/local
kubectl -n keda-demo rollout status deploy/rabbitmq --timeout=5m
kubectl -n keda-demo wait scaledobject/consumer --for=condition=Ready --timeout=3m

echo
echo "Ready. Consumers running now: $(kubectl -n keda-demo get deploy consumer -o jsonpath='{.status.replicas}' || echo 0) (expected 0)"
echo "Next: make load   (in a second terminal: make watch)"
