# 🎵 Instrumental Maker 2.0

Professional AI-powered audio stem separation and music production pipeline with a modern web interface.

## 🌟 Features

- **Multi-Engine AI Separation**: Spleeter and Demucs models for superior audio separation
- **Modern Web Dashboard**: React-based frontend with real-time job monitoring
- **Automatic Organization**: Smart music library management and cataloging
- **Production Ready**: Containerized with PostgreSQL, Redis, and Traefik integration
- **SSL & Security**: Automatic HTTPS certificates and authentication ready
- **Scalable Architecture**: Microservices design for high availability

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │     Redis       │
                    │   (Job Queue)   │
                    └─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Spleeter   │ │   Demucs    │ │Music Library│
    │  Service    │ │  Service    │ │  Organizer  │
    └─────────────┘ └─────────────┘ └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Domain name with DNS access (for production)
- Traefik reverse proxy (included in setup)

### Production Deployment

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd instrumental-maker-2.0
   ```

2. **Configure DNS**
   Add these A records to your domain:
   ```
   instrumental.yourdomain.com      A    YOUR_SERVER_IP
   instrumental-api.yourdomain.com  A    YOUR_SERVER_IP
   ```

3. **Deploy**
   ```bash
   ./deploy.sh
   ```

That's it! The system will automatically:
- Start Traefik if needed
- Build all services
- Configure SSL certificates
- Initialize the database
- Start the complete pipeline

## 📱 Access

- **Dashboard**: https://instrumental.yourdomain.com
- **API**: https://instrumental-api.yourdomain.com
- **API Docs**: https://instrumental-api.yourdomain.com/docs

## 🎛️ Services

### Core Services
- **Frontend**: Modern React dashboard for file management and monitoring
- **Backend**: FastAPI-based REST API with job queue management
- **Database**: PostgreSQL for persistent data storage
- **Redis**: Message broker and caching layer

### Processing Pipeline
- **Spleeter**: Facebook's AI model for 4-stem separation (vocals, drums, bass, other)
- **Demucs**: Meta's advanced separation model (htdemucs)
- **Music Library**: Automatic file organization and metadata management
- **Audio Reconstruction**: Advanced audio processing and enhancement

## 🔧 Management

### Basic Commands
```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Stop everything
docker-compose down

# Update deployment
./deploy.sh
```

### Service-Specific Logs
```bash
# Backend API logs
docker-compose logs -f backend

# Spleeter processing logs
docker-compose logs -f spleeter

# Database logs
docker-compose logs -f postgres
```

## 📁 Directory Structure

```
instrumental-maker-2.0/
├── dashboard-backend/     # Main API backend
├── frontend-dashboard/    # Web interface
├── services/             # Processing services
│   ├── spleeter/        # Spleeter separation service
│   ├── demucs/          # Demucs separation service
│   ├── music-library/   # Library organization
│   └── audio-reconstruction/ # Audio processing
├── data/                # Shared data volume
│   ├── input/          # Upload directory
│   ├── output/         # Processed files
│   ├── music-library/  # Organized music collection
│   └── logs/           # Application logs
├── docker-compose.yml   # Production configuration
└── deploy.sh           # Deployment script
```

## 🔒 Security

### Production Security Features
- Automatic SSL/TLS certificates via Let's Encrypt
- Secure container networking
- Non-root container users
- Optional OAuth integration
- Database connection security

### Enable Authentication (Optional)
Uncomment these lines in `docker-compose.yml`:
```yaml
# - "traefik.http.routers.instrumental.middlewares=forward-auth"
# - "traefik.http.routers.instrumental-api.middlewares=forward-auth"
```

## 🛠️ Development

### Local Development
```bash
# Start core services only
docker-compose up postgres redis

# Run backend locally
cd dashboard-backend
pip install -r requirements.txt
uvicorn main:app --reload

# Run frontend locally
cd frontend-dashboard
npm install
npm run dev
```

### Environment Variables
Key environment variables in `docker-compose.yml`:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `NEXT_PUBLIC_API_URL`: Frontend API endpoint

## 📊 Monitoring

### Health Checks
All services include health checks:
- **Database**: PostgreSQL readiness
- **Redis**: Connection test
- **Backend**: API endpoint test
- **Frontend**: Web server test
- **Processors**: Process monitoring

### Performance
- **Concurrent Processing**: Multiple separation engines
- **Persistent Storage**: PostgreSQL for reliability
- **Caching**: Redis for improved performance
- **Load Balancing**: Traefik reverse proxy

## 🔧 Troubleshooting

### Common Issues

1. **Services won't start**
   ```bash
   docker-compose down --volumes
   docker system prune -f
   ./deploy.sh
   ```

2. **SSL certificate issues**
   ```bash
   # Check Traefik logs
   docker logs traefik
   
   # Verify DNS resolution
   nslookup instrumental.yourdomain.com
   ```

3. **Processing stuck**
   ```bash
   # Check processor logs
   docker-compose logs spleeter demucs
   
   # Restart processors
   docker-compose restart spleeter demucs
   ```

### Support

For issues and feature requests, please check:
- Service logs: `docker-compose logs -f`
- Traefik dashboard: `http://your-server:8080`
- API documentation: `https://instrumental-api.yourdomain.com/docs`

## 📄 License

[Your License Here]

---

**Ready for professional music production workflows! 🎵✨**
