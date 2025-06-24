#!/bin/bash

# Store Agents Secret Setup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_status "Store Agents Secret Setup"
echo "=================================="
echo ""

# Check if required files exist
if [[ ! -f "firebase-service-account-key.json" ]]; then
    print_error "firebase-service-account-key.json not found in current directory"
    print_warning "Please ensure your Firebase service account key is in the current directory"
    exit 1
fi

# Get Google API Key
echo "Please enter your Google API Key:"
read -s GOOGLE_API_KEY
echo ""

if [[ -z "$GOOGLE_API_KEY" ]]; then
    print_error "Google API Key cannot be empty"
    exit 1
fi

# Encode values
print_status "Encoding secrets..."
ENCODED_API_KEY=$(echo -n "$GOOGLE_API_KEY" | base64)
ENCODED_SERVICE_ACCOUNT=$(cat firebase-service-account-key.json | base64 | tr -d '\n')

# Create secrets.yaml with actual values
print_status "Creating k8s/secrets.yaml with encoded values..."
cat > k8s/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: store-agents-secrets
type: Opaque
data:
  google-api-key: "$ENCODED_API_KEY"
  service-account-key: "$ENCODED_SERVICE_ACCOUNT"
EOF

print_success "Secrets file created successfully!"
print_status "You can now apply the secrets with: kubectl apply -f k8s/secrets.yaml"

# Verify the cluster connection
print_status "Checking cluster connection..."
if kubectl cluster-info &> /dev/null; then
    print_success "Connected to Kubernetes cluster"
    
    # Ask if user wants to apply secrets now
    echo ""
    read -p "Do you want to apply the secrets to your cluster now? (y/n): " apply_now
    
    if [[ "$apply_now" =~ ^[Yy]$ ]]; then
        print_status "Applying secrets to cluster..."
        kubectl apply -f k8s/secrets.yaml
        print_success "Secrets applied successfully!"
    else
        print_status "Secrets file created. Apply later with: kubectl apply -f k8s/secrets.yaml"
    fi
else
    print_warning "Not connected to a Kubernetes cluster"
    print_status "Secrets file created. Connect to your cluster and apply with: kubectl apply -f k8s/secrets.yaml"
fi

echo ""
print_success "Secret setup completed!"
