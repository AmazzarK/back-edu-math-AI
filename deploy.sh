#!/bin/bash

# EduMath AI Platform Deployment Script
# This script automates the deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
PROJECT_NAME="edu-math-ai-back"
COMPOSE_FILE="docker-compose.yml"

echo -e "${BLUE}🚀 EduMath AI Platform Deployment${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    echo "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi
    
    print_status "Docker is ready"
}

# Check if Docker Compose is available
check_docker_compose() {
    echo "Checking Docker Compose..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_status "Docker Compose is ready"
}

# Set up environment based on deployment type
setup_environment() {
    echo "Setting up environment..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
        
        # Check if .env.prod exists
        if [ ! -f ".env.prod" ]; then
            print_error ".env.prod file not found"
            echo "Please create .env.prod with production environment variables"
            exit 1
        fi
        
        # Use production environment file
        cp .env.prod .env
        print_status "Production environment configured"
    else
        # Check if .env exists
        if [ ! -f ".env" ]; then
            if [ -f ".env.example" ]; then
                cp .env.example .env
                print_warning "Created .env from .env.example - please review and update"
            else
                print_error ".env file not found and no .env.example available"
                exit 1
            fi
        fi
        print_status "Development environment configured"
    fi
}

# Build and start services
deploy_services() {
    echo "Building and starting services..."
    
    # Stop existing containers
    echo "Stopping existing containers..."
    docker-compose -f $COMPOSE_FILE down || true
    
    # Build images
    echo "Building images..."
    docker-compose -f $COMPOSE_FILE build
    
    # Start services
    echo "Starting services..."
    docker-compose -f $COMPOSE_FILE up -d
    
    print_status "Services deployed"
}

# Wait for services to be ready
wait_for_services() {
    echo "Waiting for services to be ready..."
    
    # Wait for database
    echo "Waiting for database..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f $COMPOSE_FILE exec -T db pg_isready -U edumath &> /dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Database failed to start"
        exit 1
    fi
    
    # Wait for Redis
    echo "Waiting for Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping &> /dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Redis failed to start"
        exit 1
    fi
    
    # Wait for web service
    echo "Waiting for web service..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:5000/health &> /dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_error "Web service failed to start"
        exit 1
    fi
    
    print_status "All services are ready"
}

# Initialize database
init_database() {
    echo "Initializing database..."
    
    # Run database migrations
    docker-compose -f $COMPOSE_FILE exec web python db_manager.py upgrade || true
    
    # Seed sample data in development
    if [ "$ENVIRONMENT" = "development" ]; then
        docker-compose -f $COMPOSE_FILE exec web python db_manager.py seed
    fi
    
    print_status "Database initialized"
}

# Run health checks
health_check() {
    echo "Running health checks..."
    
    # Check web service
    if curl -f http://localhost:5000/health &> /dev/null; then
        print_status "Web service health check passed"
    else
        print_error "Web service health check failed"
        return 1
    fi
    
    # Check API endpoints
    if curl -f http://localhost:5000/api/info &> /dev/null; then
        print_status "API endpoints accessible"
    else
        print_error "API endpoints not accessible"
        return 1
    fi
    
    print_status "All health checks passed"
}

# Show deployment summary
show_summary() {
    echo
    echo "=================================================="
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo "=================================================="
    echo "Environment: $ENVIRONMENT"
    echo "Services:"
    echo "  🌐 Web API: http://localhost:5000"
    echo "  🏥 Health Check: http://localhost:5000/health"
    echo "  📚 API Info: http://localhost:5000/api/info"
    
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "  🗄️  Database: localhost:5432"
        echo "  🔴 Redis: localhost:6379"
        echo
        echo "Sample accounts:"
        echo "  👑 Admin: admin@edumath-ai.com / admin123"
        echo "  👨‍🏫 Professor: prof1@edumath-ai.com / professor123"
        echo "  👩‍🎓 Student: student1@edumath-ai.com / student123"
    fi
    
    echo
    echo "Useful commands:"
    echo "  📊 View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  📈 View status: docker-compose -f $COMPOSE_FILE ps"
    echo "  🛑 Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  🔄 Restart: docker-compose -f $COMPOSE_FILE restart"
    echo "=================================================="
}

# Main deployment process
main() {
    check_docker
    check_docker_compose
    setup_environment
    deploy_services
    wait_for_services
    init_database
    
    if health_check; then
        show_summary
    else
        print_error "Deployment failed health checks"
        echo "Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "production"|"prod")
        ENVIRONMENT="production"
        main
        ;;
    "development"|"dev"|"")
        ENVIRONMENT="development"
        main
        ;;
    "stop")
        echo "Stopping services..."
        docker-compose -f docker-compose.yml down
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
        print_status "Services stopped"
        ;;
    "logs")
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    "status")
        docker-compose -f $COMPOSE_FILE ps
        ;;
    "restart")
        echo "Restarting services..."
        docker-compose -f $COMPOSE_FILE restart
        print_status "Services restarted"
        ;;
    "clean")
        echo "Cleaning up..."
        docker-compose -f docker-compose.yml down -v
        docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        docker system prune -f
        print_status "Cleanup complete"
        ;;
    *)
        echo "Usage: $0 {development|production|stop|logs|status|restart|clean}"
        echo
        echo "Commands:"
        echo "  development  - Deploy in development mode (default)"
        echo "  production   - Deploy in production mode"
        echo "  stop         - Stop all services"
        echo "  logs         - View service logs"
        echo "  status       - Show service status"
        echo "  restart      - Restart services"
        echo "  clean        - Stop services and clean up"
        exit 1
        ;;
esac
