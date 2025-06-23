# Kubernetes Deployment Order

This document outlines the correct order for deploying the recruitment application to Kubernetes.

## Prerequisites

1. Kubernetes cluster is running
2. Docker is installed and configured
3. All necessary images are built with correct environment variables

## Step 1: Build Docker Images

### Backend Image
```bash
cd backend
docker build -t matching-backend:local .
```

### AI Service Image
```bash
cd ai
docker build -t matching-ai:local .
```

### Frontend Image
```bash
cd frontend
# Frontend now uses nginx proxy - no special configuration needed
docker build -t matching-frontend:local .
```

## Step 2: Deploy to Kubernetes

Deploy in this exact order:

1. **Namespace and ConfigMaps**
   ```bash
   kubectl apply -f k8s-deploy/namespace.yaml
   kubectl apply -f k8s-deploy/secrets.yaml
   kubectl apply -f k8s-deploy/configmaps.yaml
   ```

2. **Persistent Volume Claims**
   ```bash
   kubectl apply -f k8s-deploy/local-pgdata-persistentvolumeclaim.yaml
   kubectl apply -f k8s-deploy/pgadmin-data-persistentvolumeclaim.yaml
   kubectl apply -f k8s-deploy/backend-claim0-persistentvolumeclaim.yaml
   kubectl apply -f k8s-deploy/ai-claim0-persistentvolumeclaim.yaml
   ```

3. **Database Services**
   ```bash
   kubectl apply -f k8s-deploy/db-service.yaml
   kubectl apply -f k8s-deploy/db-pod.yaml
   ```

4. **Wait for Database to be Ready**
   ```bash
   kubectl wait --for=condition=ready pod -l app=postgres-service -n recruitment-app --timeout=300s
   ```

5. **Backend Services**
   ```bash
   kubectl apply -f k8s-deploy/backend-service.yaml
   kubectl apply -f k8s-deploy/backend-pod.yaml
   ```

6. **Wait for Backend to be Ready**
   ```bash
   kubectl wait --for=condition=ready pod -l app=backend-service -n recruitment-app --timeout=300s
   ```

7. **AI Services**
   ```bash
   kubectl apply -f k8s-deploy/ai-service.yaml
   kubectl apply -f k8s-deploy/ai-pod.yaml
   ```

8. **Frontend Services**
   ```bash
   kubectl apply -f k8s-deploy/frontend-service.yaml
   kubectl apply -f k8s-deploy/frontend-pod.yaml
   ```

9. **PgAdmin (Optional)**
   ```bash
   kubectl apply -f k8s-deploy/pgadmin-service.yaml
   kubectl apply -f k8s-deploy/pgadmin-pod.yaml
   ```

## Step 3: Verify Deployment

1. **Check all pods are running**
   ```bash
   kubectl get pods -n recruitment-app
   ```

2. **Check services and get external IPs**
   ```bash
   kubectl get services -n recruitment-app
   ```

3. **Get frontend and backend URLs**
   ```bash
   # Frontend URL
   kubectl get service frontend-service -n recruitment-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}'
   
   # Backend URL  
   kubectl get service backend-service -n recruitment-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}:{.spec.ports[0].port}'
   ```

## Important Notes

### Frontend API Configuration Issue Fix

The main issue was that the frontend was not connecting to the backend service because:

1. **Vite Environment Variables**: Vite embeds environment variables at build time, not runtime
2. **Cluster-Internal Communication**: Frontend needs to communicate with backend using internal Kubernetes DNS names
3. **Security**: Backend should only be accessible from within the cluster, not externally

### Solution Applied

1. **Created `frontend/nginx.conf`**: Nginx configuration that proxies API requests to backend service
2. **Modified `frontend/Dockerfile`**: Multi-stage build with nginx to serve static files and proxy API requests
3. **Updated `frontend/src/services/api.js`**: Smart API URL detection (relative URLs for Kubernetes, localhost for development)
4. **Updated `k8s-deploy/backend-service.yaml`**: Kept as `ClusterIP` for internal cluster access only
5. **Updated `k8s-deploy/configmaps.yaml`**: Removed VITE_API_URL since nginx handles proxying

### Security Benefits

1. **Backend Isolation**: Backend is only accessible from within the Kubernetes cluster
2. **No External Exposure**: Backend service uses `ClusterIP` type, preventing external access
3. **Nginx Proxy**: Frontend nginx proxies API requests to backend using internal Kubernetes DNS
4. **Client-Side Security**: Browser never directly communicates with backend, all requests go through nginx proxy
5. **Network Policies**: Can be easily extended with Kubernetes NetworkPolicies for additional security

## Troubleshooting

If the frontend still can't connect to the backend:

1. **Check if backend service is accessible**:
   ```bash
   kubectl port-forward service/backend-service 8017:8017 -n recruitment-app
   ```

2. **Verify frontend is using correct API URL**:
   - Check browser developer tools → Network tab
   - Look for API calls and verify the URL being used

3. **Check nginx proxy and backend connectivity**:
   ```bash
   # Check frontend logs (nginx logs)
   kubectl logs -n recruitment-app deployment/frontend-deployment
   
   # Test nginx proxy from within the frontend pod
   kubectl exec -n recruitment-app deployment/frontend-deployment -- curl -v http://localhost:8080/api/v1/
   
   # Test backend service connectivity from frontend pod
   kubectl exec -n recruitment-app deployment/frontend-deployment -- curl -v http://backend-service.recruitment-app.svc.cluster.local:8017/api/v1/
   
   # Restart frontend deployment
   kubectl rollout restart deployment frontend-deployment -n recruitment-app
   ``` 