#!/usr/bin/env bash
# Publish a burst of jobs (default 300 x 1s of work) and let KEDA react.
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl -n keda-demo delete job producer --ignore-not-found --wait=true >/dev/null
kubectl apply -k k8s/overlays/local-load-test
kubectl -n keda-demo wait job/producer --for=condition=Complete --timeout=3m
kubectl -n keda-demo logs job/producer
