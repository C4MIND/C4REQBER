#!/usr/bin/env bash
# Deploy c4reqber API + PostgreSQL to Kubernetes (production layout).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "c4reqber v5.6.0 — Kubernetes Deployment"
echo "=========================================="

if [[ ! -f secrets.yaml ]]; then
  echo "ERROR: k8s/secrets.yaml missing."
  echo "Copy secrets.example.yaml → secrets.yaml and fill real values."
  exit 1
fi

echo "Applying manifests..."
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

echo "Waiting for postgres..."
kubectl rollout status statefulset/postgres -n c4reqber --timeout=180s

echo "Waiting for API..."
kubectl rollout status deployment/c4reqber-api -n c4reqber --timeout=180s

echo
echo "Deployment complete."
kubectl get pods,svc -n c4reqber
echo
echo "Port-forward API:"
echo "  kubectl port-forward svc/c4reqber-api 8000:80 -n c4reqber"
echo "Health:"
echo "  curl http://127.0.0.1:8000/api/v1/health"