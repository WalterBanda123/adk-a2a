#!/bin/bash

# Test script for Store Agents deployment
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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get external IP
print_status "Getting external IP from ingress..."
EXTERNAL_IP=$(kubectl get ingress store-agents-ingress --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")

if [[ -z "$EXTERNAL_IP" ]]; then
    print_error "External IP not found. Make sure your ingress is ready."
    echo "You can check with: kubectl get ingress store-agents-ingress"
    exit 1
fi

print_status "External IP: $EXTERNAL_IP"

# Test health endpoint
print_status "Testing health endpoint..."
if curl -f "http://$EXTERNAL_IP/health" > /dev/null 2>&1; then
    print_success "Health check passed!"
else
    print_error "Health check failed!"
    exit 1
fi

# Test main API endpoint
print_status "Testing main API endpoint..."
response=$(curl -s -X POST "http://$EXTERNAL_IP/run" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello", "user_id": "test-user", "context": {}}')

if [[ $? -eq 0 ]]; then
    print_success "API endpoint is responding!"
    echo "Response: $response"
else
    print_error "API endpoint test failed!"
    exit 1
fi

print_success "All tests passed! Your Store Agents app is ready!"
echo ""
echo "🌐 Your app is accessible at: http://$EXTERNAL_IP"
echo "📊 Health check: http://$EXTERNAL_IP/health"
echo "🚀 API endpoint: http://$EXTERNAL_IP/run"
