#!/bin/bash

# Smart Meter Microservices Deployment Script
# This script automates the deployment of FilterReading and ConvertReading services

echo "=== Smart Meter Microservices Deployment ==="
echo ""

# Check if REPO path is set
if [ -z "$REPO" ]; then
    echo "Error: REPO environment variable is not set."
    echo "Please set it with: export REPO=<your-artifact-registry-repo-path>"
    echo "Example: export REPO=northamerica-northeast2-docker.pkg.dev/your-project/sofe4630u"
    exit 1
fi

# Get project ID
PROJECT=$(gcloud config list project --format "value(core.project)")
if [ -z "$PROJECT" ]; then
    echo "Error: Could not determine GCP project ID."
    echo "Please ensure you are authenticated with gcloud."
    exit 1
fi

echo "Using GCP Project: $PROJECT"
echo "Using Repository: $REPO"
echo ""

# Set image names
FILTER_IMAGE=$REPO/filter-reading
CONVERT_IMAGE=$REPO/convert-reading

echo "=== Step 1: Building and Pushing FilterReading Service ==="
cd ~/SOFE4630U-MS4/filter_reading || exit 1

# Check for JSON credential file
if ! ls *.json 1> /dev/null 2>&1; then
    echo "Warning: No JSON credential file found in filter_reading directory"
    echo "Please copy your service account key file to this directory"
    exit 1
fi

echo "Building FilterReading image..."
gcloud builds submit -t $FILTER_IMAGE
if [ $? -ne 0 ]; then
    echo "Error: Failed to build FilterReading image"
    exit 1
fi

echo ""
echo "=== Step 2: Building and Pushing ConvertReading Service ==="
cd ~/SOFE4630U-MS4/convert_reading || exit 1

# Check for JSON credential file
if ! ls *.json 1> /dev/null 2>&1; then
    echo "Warning: No JSON credential file found in convert_reading directory"
    echo "Please copy your service account key file to this directory"
    exit 1
fi

echo "Building ConvertReading image..."
gcloud builds submit -t $CONVERT_IMAGE
if [ $? -ne 0 ]; then
    echo "Error: Failed to build ConvertReading image"
    exit 1
fi

echo ""
echo "=== Step 3: Deploying FilterReading to GKE ==="
cd ~/SOFE4630U-MS4/filter_reading || exit 1
PROJECT=$PROJECT FILTER_IMAGE=$FILTER_IMAGE envsubst < filter.yaml | kubectl apply -f -
if [ $? -ne 0 ]; then
    echo "Error: Failed to deploy FilterReading service"
    exit 1
fi

echo ""
echo "=== Step 4: Deploying ConvertReading to GKE ==="
cd ~/SOFE4630U-MS4/convert_reading || exit 1
PROJECT=$PROJECT CONVERT_IMAGE=$CONVERT_IMAGE envsubst < convert.yaml | kubectl apply -f -
if [ $? -ne 0 ]; then
    echo "Error: Failed to deploy ConvertReading service"
    exit 1
fi

echo ""
echo "=== Step 5: Verifying Deployment ==="
echo "Waiting for pods to start..."
sleep 10

kubectl get pods -l app=filter-reading
kubectl get pods -l app=convert-reading

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "To view logs:"
echo "  kubectl logs -l app=filter-reading -f"
echo "  kubectl logs -l app=convert-reading -f"
echo ""
echo "To run the meter simulator:"
echo "  cd ~/SOFE4630U-MS4/meter_simulator"
echo "  python main.py"
echo ""
