#!/bin/bash

# Deploy Instrumental Maker with Traefik Integration
# This script deploys the instrumental maker dashboard with Traefik reverse proxy

echo "🎵 Deploying Instrumental Maker with Traefik Integration..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if Traefik is running
echo "📋 Checking Traefik status..."
if ! docker ps | grep -q traefik; then
    echo "⚠️  Traefik is not running. Please start Traefik first:"
    echo "   cd ~/homelab/stacks/traefik && docker-compose up -d"
    exit 1
fi

# Check if web network exists
if ! docker network ls | grep -q web; then
    echo "🌐 Creating web network for Traefik..."
    docker network create web
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.traefik.yml down

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose -f docker-compose.traefik.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.traefik.yml ps

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📱 Access URLs:"
echo "   Frontend Dashboard: https://instrumental.vectorhost.net"
echo "   Backend API: https://instrumental-api.vectorhost.net"
echo "   API Documentation: https://instrumental-api.vectorhost.net/docs"
echo ""
echo "🔒 Security Note:"
echo "   Uncomment the authentication middleware lines in docker-compose.traefik.yml"
echo "   to enable OAuth protection via your forward-auth setup."
echo ""
echo "🔍 Troubleshooting:"
echo "   - Check logs: docker-compose -f docker-compose.traefik.yml logs -f"
echo "   - Check Traefik dashboard: http://localhost:8080"
echo "   - Verify DNS points to your server's IP address"
