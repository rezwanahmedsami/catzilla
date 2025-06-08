#!/bin/bash
# Docker Development Helper Script for Catzilla
# Provides easy access to interactive development environments

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

print_usage() {
    echo -e "${YELLOW}Catzilla Docker Development Helper${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  shell [linux|windows]    Open interactive shell in container"
    echo "  build [linux|windows]    Build Docker images"
    echo "  test  [linux|windows]    Run tests in containers"
    echo "  clean                     Clean Docker images and volumes"
    echo "  logs  [linux|windows]    View container logs"
    echo ""
    echo "Examples:"
    echo "  $0 shell linux           # Interactive Linux development"
    echo "  $0 build windows         # Build Windows container"
    echo "  $0 test                   # Test on all platforms"
    echo "  $0 clean                  # Clean all Docker resources"
}

build_images() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Building Linux development image...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-dev-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Building Windows development image...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-dev-windows
            ;;
        "all"|"")
            echo -e "${GREEN}🌍 Building all development images...${NC}"
            docker-compose -f docker/docker-compose.yml build catzilla-dev-linux catzilla-dev-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            return 1
            ;;
    esac
}

open_shell() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux"|"")
            echo -e "${GREEN}🐧 Opening Linux development shell...${NC}"
            echo "Type 'exit' to leave the container"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-dev-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Opening Windows development shell...${NC}"
            echo "Type 'exit' to leave the container"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-dev-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            return 1
            ;;
    esac
}

run_tests() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux")
            echo -e "${GREEN}🐧 Running tests on Linux...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Running tests on Windows...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            ;;
        "all"|"")
            echo -e "${GREEN}🌍 Running tests on all platforms...${NC}"
            docker-compose -f docker/docker-compose.yml run --rm catzilla-linux
            docker-compose -f docker/docker-compose.yml run --rm catzilla-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            return 1
            ;;
    esac
}

clean_docker() {
    cd "$PROJECT_ROOT"
    echo -e "${YELLOW}🧹 Cleaning Docker resources...${NC}"

    # Stop and remove containers
    docker-compose -f docker/docker-compose.yml down --volumes --remove-orphans

    # Remove Docker images
    echo "Removing Catzilla Docker images..."
    docker images | grep catzilla | awk '{print $3}' | xargs -r docker rmi -f

    # Remove unused volumes
    echo "Removing unused Docker volumes..."
    docker volume prune -f

    echo -e "${GREEN}✅ Docker cleanup complete!${NC}"
}

view_logs() {
    local platform=$1
    cd "$PROJECT_ROOT"

    case "$platform" in
        "linux"|"")
            echo -e "${GREEN}🐧 Viewing Linux container logs...${NC}"
            docker-compose -f docker/docker-compose.yml logs catzilla-linux
            ;;
        "windows")
            echo -e "${GREEN}🪟 Viewing Windows container logs...${NC}"
            docker-compose -f docker/docker-compose.yml logs catzilla-windows
            ;;
        *)
            echo -e "${RED}❌ Unknown platform: $platform${NC}"
            return 1
            ;;
    esac
}

# Main command dispatcher
case "$1" in
    "shell")
        open_shell "$2"
        ;;
    "build")
        build_images "$2"
        ;;
    "test")
        run_tests "$2"
        ;;
    "clean")
        clean_docker
        ;;
    "logs")
        view_logs "$2"
        ;;
    "help"|"--help"|"-h"|"")
        print_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        print_usage
        exit 1
        ;;
esac
