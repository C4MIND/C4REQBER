#!/bin/bash
# Deploy TURBO-CDI v6.0 to Kubernetes

set -e

echo "=========================================="
echo "TURBO-CDI v6.0 - Kubernetes Deployment"
echo "=========================================="
echo

# Build image
echo "Building Docker image..."
docker build -t turbo-cdi:v6.0.0 .

# Apply K8s manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

# Wait for rollout
echo "Waiting for deployment to complete..."
kubectl rollout status deployment/turbo-cdi-engine -n turbo-cdi --timeout=120s

# Show status
echo
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo
echo "Services:"
kubectl get svc -n turbo-cdi
echo
echo "Pods:"
kubectl get pods -n turbo-cdi
echo
echo "Access the API at:"
echo "  kubectl port-forward svc/turbo-cdi-engine 8000:80 -n turbo-cdi"
echo
