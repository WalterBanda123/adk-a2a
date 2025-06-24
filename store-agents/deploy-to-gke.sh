#!/bin/bash

# Store Agents GKE Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_ID=""
CLUSTER_NAME=""
ZONE=""
REGION=""
IMAGE_NAME="store-agents"
IMAGE_TAG="latest"

# Function to show usage
show_usage() {
    echo "Usage: $0 --project-id=PROJECT_ID --cluster-name=CLUSTER_NAME --zone=ZONE [OPTIONS]"
    echo ""
    echo "Required options:"
    echo "  --project-id=PROJECT_ID     Your GCP project ID"
    echo "  --cluster-name=CLUSTER_NAME Your GKE cluster name"
    echo "  --zone=ZONE                 GKE cluster zone (e.g., us-central1-a)"
    echo ""
    echo "Optional options:"
    echo "  --region=REGION             Use region instead of zone (for regional clusters)"
    echo "  --image-tag=TAG             Docker image tag (default: latest)"
    echo "  --help                      Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --project-id=my-project --cluster-name=my-cluster --zone=us-central1-a"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id=*)
            PROJECT_ID="${1#*=}"
            shift
            ;;
        --cluster-name=*)
            CLUSTER_NAME="${1#*=}"
            shift
            ;;
        --zone=*)
            ZONE="${1#*=}"
            shift
            ;;
        --region=*)
            REGION="${1#*=}"
            shift
            ;;
        --image-tag=*)
            IMAGE_TAG="${1#*=}"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROJECT_ID" || -z "$CLUSTER_NAME" || (-z "$ZONE" && -z "$REGION") ]]; then
    print_error "Missing required parameters"
    show_usage
    exit 1
fi

# Set location parameter
if [[ -n "$REGION" ]]; then
    LOCATION_PARAM="--region=$REGION"
    LOCATION="$REGION"
else
    LOCATION_PARAM="--zone=$ZONE"
    LOCATION="$ZONE"
fi

print_status "Starting deployment to GKE cluster..."
echo "Project ID: $PROJECT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Location: $LOCATION"
echo "Image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
echo ""

# Step 1: Set up gcloud configuration
print_status "Setting up gcloud configuration..."
gcloud config set project $PROJECT_ID
gcloud config set compute/zone $LOCATION

# Step 2: Enable required APIs
print_status "Ensuring required APIs are enabled..."
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Step 3: Configure Docker for GCR
print_status "Configuring Docker for Google Container Registry..."
gcloud auth configure-docker

# Step 4: Build and push Docker image
print_status "Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG .

print_status "Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG

print_success "Docker image pushed successfully!"

# Step 5: Get cluster credentials
print_status "Getting GKE cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME $LOCATION_PARAM

# Step 6: Update deployment YAML with correct project ID
print_status "Updating Kubernetes manifests..."
sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" k8s/deployment.yaml
rm k8s/deployment.yaml.bak

# Step 7: Create secrets (if they don't exist)
print_status "Checking for existing secrets..."
if ! kubectl get secret store-agents-secrets &> /dev/null; then
    print_warning "Secret 'store-agents-secrets' not found."
    print_warning "Please create the secret manually with your API keys before proceeding."
    print_warning "You can use the template in k8s/secrets.yaml"
    echo ""
    echo "To create the secret, run:"
    echo "1. Base64 encode your Google API key:"
    echo "   echo -n 'your-google-api-key' | base64"
    echo ""
    echo "2. Base64 encode your service account JSON:"
    echo "   cat firebase-service-account-key.json | base64 -w 0"
    echo ""
    echo "3. Update k8s/secrets.yaml with the encoded values"
    echo "4. Apply the secret:"
    echo "   kubectl apply -f k8s/secrets.yaml"
    echo ""
    read -p "Press Enter after creating the secret to continue..."
else
    print_success "Secret 'store-agents-secrets' already exists"
fi

# Step 8: Deploy to Kubernetes
print_status "Deploying to Kubernetes..."

# Apply secrets first (if updated)
if kubectl get secret store-agents-secrets &> /dev/null; then
    print_status "Secret already exists, skipping secret creation"
else
    print_status "Applying secrets..."
    kubectl apply -f k8s/secrets.yaml
fi

# Apply main deployment
print_status "Applying deployment..."
kubectl apply -f k8s/deployment.yaml

# Optional: Apply SSL certificate if using custom domain
if [[ -f "k8s/ssl-certificate.yaml" ]]; then
    print_status "Applying SSL certificate..."
    kubectl apply -f k8s/ssl-certificate.yaml
fi

# Step 9: Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
kubectl rollout status deployment/store-agents-app

# Step 10: Get service information
print_status "Getting service information..."
kubectl get services store-agents-service

# Step 11: Get ingress information
print_status "Getting ingress information..."
kubectl get ingress store-agents-ingress

# Step 12: Get external IP
print_status "Getting external IP (this may take a few minutes)..."
external_ip=""
while [ -z $external_ip ]; do
    echo "Waiting for external IP..."
    external_ip=$(kubectl get ingress store-agents-ingress --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
    [ -z "$external_ip" ] && sleep 10
done

print_success "Deployment completed successfully!"
echo ""
echo "=== Deployment Summary ==="
echo "External IP: $external_ip"
echo "Health Check: http://$external_ip/health"
echo "API Endpoint: http://$external_ip/run"
echo ""
echo "To test your deployment:"
echo "curl http://$external_ip/health"
echo ""
echo "To check logs:"
echo "kubectl logs -f deployment/store-agents-app"
echo ""
echo "To scale your deployment:"
echo "kubectl scale deployment store-agents-app --replicas=3"

print_success "Store Agents successfully deployed to GKE!"
