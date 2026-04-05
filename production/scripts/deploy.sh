#!/bin/bash
# Deployment Script for Customer Success FTE
# Deploys the application to Kubernetes

set -e

# Configuration
NAMESPACE="customer-success-fte"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-your-registry}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
APP_NAME="customer-success-fte"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please configure kubectl first."
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build API image
    log_info "Building API image..."
    docker build -t ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG} -f Dockerfile .
    
    # Build Worker image
    log_info "Building Worker image..."
    docker build -t ${IMAGE_REGISTRY}/${APP_NAME}-worker:${IMAGE_TAG} -f Dockerfile.worker .
    
    log_success "Docker images built successfully"
}

# Push images to registry
push_images() {
    log_info "Pushing images to registry..."
    
    docker push ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
    docker push ${IMAGE_REGISTRY}/${APP_NAME}-worker:${IMAGE_TAG}
    
    log_success "Images pushed to registry"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace..."
    
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Namespace created"
}

# Apply Kubernetes manifests
apply_manifests() {
    log_info "Applying Kubernetes manifests..."
    
    # Apply in order
    kubectl apply -f k8s/00-namespace.yaml
    kubectl apply -f k8s/01-configmap.yaml
    kubectl apply -f k8s/02-secrets.yaml
    kubectl apply -f k8s/03-database-statefulset.yaml
    kubectl apply -f k8s/04-kafka-deployment.yaml
    kubectl apply -f k8s/05-api-deployment.yaml
    kubectl apply -f k8s/06-worker-deployment.yaml
    kubectl apply -f k8s/07-services.yaml
    kubectl apply -f k8s/08-ingress.yaml
    kubectl apply -f k8s/09-hpa.yaml
    kubectl apply -f k8s/10-network-policy.yaml
    kubectl apply -f k8s/11-service-account.yaml
    
    log_success "Kubernetes manifests applied"
}

# Wait for deployments
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."
    
    # Wait for API deployment
    log_info "Waiting for API deployment..."
    kubectl rollout status deployment/fte-api -n ${NAMESPACE} --timeout=300s
    
    # Wait for worker deployment
    log_info "Waiting for worker deployment..."
    kubectl rollout status deployment/fte-message-processor -n ${NAMESPACE} --timeout=300s
    
    # Wait for database
    log_info "Waiting for database..."
    kubectl rollout status statefulset/postgres -n ${NAMESPACE} --timeout=300s
    
    # Wait for Kafka
    log_info "Waiting for Kafka..."
    kubectl rollout status deployment/kafka -n ${NAMESPACE} --timeout=300s
    
    log_success "All deployments ready"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Create migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  namespace: ${NAMESPACE}
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
        command: ["python", "scripts/migrate.py", "up"]
        envFrom:
        - configMapRef:
            name: fte-config
        - secretRef:
            name: fte-secrets
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for migration to complete
    kubectl wait --for=condition=complete job/db-migrate -n ${NAMESPACE} --timeout=120s
    
    log_success "Database migrations complete"
}

# Seed knowledge base
seed_knowledge() {
    log_info "Seeding knowledge base..."
    
    # Create seed job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: seed-kb
  namespace: ${NAMESPACE}
spec:
  template:
    spec:
      containers:
      - name: seed
        image: ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
        command: ["python", "scripts/seed_kb.py"]
        envFrom:
        - configMapRef:
            name: fte-config
        - secretRef:
            name: fte-secrets
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for seeding to complete
    kubectl wait --for=condition=complete job/seed-kb -n ${NAMESPACE} --timeout=300s
    
    log_success "Knowledge base seeded"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pods are running
    log_info "Checking pod status..."
    kubectl get pods -n ${NAMESPACE}
    
    # Check services
    log_info "Checking services..."
    kubectl get svc -n ${NAMESPACE}
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    sleep 10
    
    # Port-forward to API
    kubectl port-forward svc/customer-success-fte -n ${NAMESPACE} 8000:80 &
    PORT_FORWARD_PID=$!
    
    sleep 5
    
    # Test health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_success "Health check passed"
    else
        log_warning "Health check failed (may need more time to start)"
    fi
    
    # Kill port-forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    log_success "Deployment verified"
}

# Cleanup old jobs
cleanup() {
    log_info "Cleaning up old jobs..."
    
    kubectl delete job db-migrate -n ${NAMESPACE} --ignore-not-found
    kubectl delete job seed-kb -n ${NAMESPACE} --ignore-not-found
    
    log_success "Cleanup complete"
}

# Main deployment function
deploy() {
    log_info "========================================="
    log_info "Deploying ${APP_NAME}"
    log_info "========================================="
    log_info "Namespace: ${NAMESPACE}"
    log_info "Image Registry: ${IMAGE_REGISTRY}"
    log_info "Image Tag: ${IMAGE_TAG}"
    log_info "========================================="
    echo ""
    
    check_prerequisites
    build_images
    push_images
    create_namespace
    apply_manifests
    wait_for_deployments
    run_migrations
    seed_knowledge
    verify_deployment
    cleanup
    
    echo ""
    log_success "========================================="
    log_success "Deployment complete!"
    log_success "========================================="
    log_success "API: kubectl port-forward svc/customer-success-fte -n ${NAMESPACE} 8000:80"
    log_success "Docs: http://localhost:8000/docs"
    log_success "Health: http://localhost:8000/health"
    log_success "========================================="
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/fte-api -n ${NAMESPACE}
    kubectl rollout undo deployment/fte-message-processor -n ${NAMESPACE}
    
    log_success "Rollback complete"
}

# Show status
status() {
    log_info "Deployment Status:"
    echo ""
    
    kubectl get pods -n ${NAMESPACE}
    echo ""
    kubectl get svc -n ${NAMESPACE}
    echo ""
    kubectl get deployments -n ${NAMESPACE}
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    build)
        check_prerequisites
        build_images
        ;;
    push)
        push_images
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|build|push}"
        exit 1
        ;;
esac
