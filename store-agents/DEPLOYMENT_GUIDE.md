# 🚀 Store Agents GKE Deployment Guide

This guide will help you containerize and deploy your Store Agents application to Google Kubernetes Engine (GKE).

## 📋 Prerequisites

1. **GCP Project**: Ensure you have a GCP project with billing enabled
2. **GKE Cluster**: Create a GKE cluster in your project
3. **Docker**: Docker installed on your local machine
4. **gcloud CLI**: Google Cloud CLI installed and authenticated
5. **kubectl**: Kubernetes CLI tool
6. **API Keys**: Google API Key and Firebase service account key

## 🔧 Quick Setup

### 1. Get Your Cluster Information

First, get your GKE cluster details:

```bash
# List your clusters
gcloud container clusters list

# Get cluster info (replace with your values)
CLUSTER_NAME="your-cluster-name"
ZONE="your-zone"  # e.g., us-central1-a
PROJECT_ID="your-project-id"
```

### 2. Set Up Secrets

Run the secrets setup script to encode your API keys:

```bash
# Make sure you have firebase-service-account-key.json in this directory
./setup-secrets.sh
```

This script will:
- Prompt for your Google API Key
- Encode your Firebase service account key
- Create the Kubernetes secrets file
- Optionally apply it to your cluster

### 3. Deploy to GKE

Run the deployment script:

```bash
./deploy-to-gke.sh --project-id=YOUR_PROJECT_ID --cluster-name=YOUR_CLUSTER_NAME --zone=YOUR_ZONE
```

Example:
```bash
./deploy-to-gke.sh --project-id=my-store-project --cluster-name=store-cluster --zone=us-central1-a
```

For regional clusters, use `--region` instead of `--zone`:
```bash
./deploy-to-gke.sh --project-id=my-store-project --cluster-name=store-cluster --region=us-central1
```

## 🔄 Manual Deployment Steps

If you prefer to run commands manually:

### 1. Build and Push Docker Image

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Configure Docker for GCR
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/$PROJECT_ID/store-agents:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/store-agents:latest
```

### 2. Connect to Your Cluster

```bash
# Get cluster credentials
gcloud container clusters get-credentials YOUR_CLUSTER_NAME --zone=YOUR_ZONE --project=YOUR_PROJECT_ID
```

### 3. Update Deployment Configuration

```bash
# Update the deployment.yaml with your project ID
sed -i "s/PROJECT_ID/$PROJECT_ID/g" k8s/deployment.yaml
```

### 4. Apply Kubernetes Manifests

```bash
# Apply secrets (after running setup-secrets.sh)
kubectl apply -f k8s/secrets.yaml

# Apply deployment, service, and ingress
kubectl apply -f k8s/deployment.yaml

# Optional: Apply SSL certificate for custom domain
kubectl apply -f k8s/ssl-certificate.yaml
```

### 5. Check Deployment Status

```bash
# Check if pods are running
kubectl get pods

# Check deployment status
kubectl rollout status deployment/store-agents-app

# Get service info
kubectl get services

# Get ingress info (external IP)
kubectl get ingress
```

## 🌐 Accessing Your Application

### Get External IP

```bash
# Get the external IP from ingress
kubectl get ingress store-agents-ingress

# Or watch until IP is assigned
kubectl get ingress store-agents-ingress --watch
```

### Test Your Deployment

```bash
# Replace EXTERNAL_IP with your actual external IP
curl http://EXTERNAL_IP/health

# Test the main API endpoint
curl -X POST http://EXTERNAL_IP/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test-user"}'
```

## 🔍 Monitoring and Troubleshooting

### View Logs

```bash
# View logs from all pods
kubectl logs -f deployment/store-agents-app

# View logs from a specific pod
kubectl logs -f <pod-name>

# Get pod names
kubectl get pods -l app=store-agents
```

### Scale Your Application

```bash
# Scale to 3 replicas
kubectl scale deployment store-agents-app --replicas=3

# Check scaling status
kubectl get pods -l app=store-agents
```

### Update Your Application

```bash
# Build and push new image
docker build -t gcr.io/$PROJECT_ID/store-agents:v2 .
docker push gcr.io/$PROJECT_ID/store-agents:v2

# Update deployment with new image
kubectl set image deployment/store-agents-app store-agents=gcr.io/$PROJECT_ID/store-agents:v2

# Watch rollout
kubectl rollout status deployment/store-agents-app
```

### Debug Issues

```bash
# Describe deployment
kubectl describe deployment store-agents-app

# Describe service
kubectl describe service store-agents-service

# Describe ingress
kubectl describe ingress store-agents-ingress

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

## 🔐 Security Considerations

1. **Secrets Management**: Your API keys are stored as Kubernetes secrets
2. **Network Policies**: Consider implementing network policies for additional security
3. **RBAC**: Configure Role-Based Access Control for your cluster
4. **SSL/TLS**: Use the provided SSL certificate configuration for HTTPS

## 🌍 Custom Domain Setup

1. **Reserve Static IP** (optional):
   ```bash
   gcloud compute addresses create store-agents-ip --global
   ```

2. **Update DNS**: Point your domain to the external IP

3. **Update Configuration**: 
   - Modify `k8s/deployment.yaml` ingress section with your domain
   - Update `k8s/ssl-certificate.yaml` with your domain

4. **Apply SSL Certificate**:
   ```bash
   kubectl apply -f k8s/ssl-certificate.yaml
   ```

## 📊 Monitoring Dashboard

Access GKE monitoring in the Google Cloud Console:
1. Go to Kubernetes Engine > Workloads
2. Click on your `store-agents-app` deployment
3. View metrics, logs, and health status

## 🔄 CI/CD Integration

For automated deployments, consider setting up:
1. **Cloud Build** for automated Docker image building
2. **GitHub Actions** or **Cloud Build triggers** for automated deployments
3. **Helm charts** for more complex configuration management

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GKE documentation
3. Check application logs for specific errors
4. Verify all secrets and environment variables are correctly set

## 🎉 Congratulations!

Your Store Agents application is now running on GKE! You can access it via the external IP and integrate it with your Firebase frontend.

Remember to:
- Monitor resource usage and scale as needed
- Set up proper backup strategies
- Implement monitoring and alerting
- Keep your dependencies updated
