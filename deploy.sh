#!/bin/bash

# Production Deployment Script for Instrumental Maker
# This script deploys the complete instrumental maker pipeline

set -e  # Exit on any error

echo "🎵 Deploying Instrumental Maker Production Stack..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

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

# Check if Traefik is running
print_status "Checking Traefik status..."
if ! docker ps | grep -q traefik; then
    print_warning "Traefik is not running. Starting Traefik first..."
    cd ~/homelab/stacks/traefik
    docker compose up -d
    cd - > /dev/null
    sleep 5
fi

# Check if web network exists
if ! docker network ls | grep -q web; then
    print_status "Creating web network for Traefik..."
    docker network create web
fi

# Ensure data directories exist
print_status "Creating data directories..."
mkdir -p data/{input,output,logs,music-library,reconstructed,db-init}

# Stop any existing services
print_status "Stopping existing services..."
docker compose down --remove-orphans

# Pull latest images
print_status "Pulling latest base images..."
docker compose pull postgres redis

# Build and start all services
print_status "Building and starting all services..."
docker compose up -d --build

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check service health
print_status "Checking service health..."

services=("postgres" "redis" "backend" "frontend" "spleeter" "demucs" "music-library" "audio-reconstruction")
all_healthy=true

for service in "${services[@]}"; do
    if docker compose ps "$service" | grep -q "Up (healthy)"; then
        print_success "$service is healthy"
    elif docker compose ps "$service" | grep -q "Up"; then
        print_warning "$service is running but health check pending"
    else
        print_error "$service is not running properly"
        all_healthy=false
    fi
done

# Show service status
echo ""
print_status "Service Status:"
docker compose ps

echo ""
if [ "$all_healthy" = true ]; then
    print_success "🎉 Deployment Complete! All services are running."
else
    print_warning "Some services may need more time to start. Check logs with: docker compose logs -f"
fi

echo ""
echo "📱 Access URLs:"
echo "   Frontend Dashboard: https://instrumental.vectorhost.net"
echo "   Backend API: https://instrumental-api.vectorhost.net"
echo "   API Documentation: https://instrumental-api.vectorhost.net/docs"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker compose logs -f [service_name]"
echo "   Restart: docker compose restart [service_name]"
echo "   Stop: docker compose down"
echo "   Update: ./deploy.sh"
echo ""
echo "📊 Pipeline Services:"
echo "   - Spleeter: AI stem separation (4-stem model)"
echo "   - Demucs: Advanced stem separation (htdemucs model)"
echo "   - Music Library: Automatic organization and cataloging"
echo "   - Audio Reconstruction: Advanced audio processing"
echo ""
print_success "Ready for production use! 🚀"
