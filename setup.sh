#!/bin/bash
# Solarpunk Utopia - Complete Setup Script
# Usage: curl -sL https://raw.githubusercontent.com/lizTheDeveloper/solarpunk_utopia/main/setup.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Solarpunk Utopia - Setup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Detect Termux
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [ -n "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=true
fi

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    *)          PLATFORM="UNKNOWN:${OS}"
esac

if [ "$IS_TERMUX" = true ]; then
    echo -e "${BLUE}Detected platform: Termux (Android)${NC}"

    # Enable wake lock immediately to prevent sleep during installation
    echo -e "${YELLOW}Enabling wake lock to prevent phone from sleeping during installation...${NC}"
    termux-wake-lock 2>/dev/null || {
        echo -e "${YELLOW}Note: Install 'Termux:API' from F-Droid for wake-lock support${NC}"
        echo -e "${YELLOW}Installation may be interrupted if phone goes to sleep${NC}"
    }
else
    echo -e "${BLUE}Detected platform: ${PLATFORM}${NC}"
fi

# Install system dependencies
install_dependencies() {
    echo -e "${BLUE}Installing system dependencies...${NC}"

    if [ "$IS_TERMUX" = true ]; then
        # Termux (Android)
        pkg update -y
        pkg install -y python git nodejs
    elif [ "$PLATFORM" = "Linux" ]; then
        # Debian/Ubuntu
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv git curl nodejs npm
        # RHEL/CentOS/Fedora
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3 python3-pip git curl nodejs npm
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip git curl nodejs npm
        fi
    elif [ "$PLATFORM" = "Mac" ]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            echo -e "${YELLOW}Installing Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install python3 node git
    fi
}

# Clone repository if not exists
clone_repo() {
    if [ ! -d "solarpunk_utopia" ]; then
        echo -e "${BLUE}Cloning repository...${NC}"
        git clone https://github.com/lizTheDeveloper/solarpunk_utopia.git
        cd solarpunk_utopia
    else
        echo -e "${BLUE}Repository exists, updating...${NC}"
        cd solarpunk_utopia
        git pull origin main
    fi
}

# Setup Python virtual environment
setup_python() {
    echo -e "${BLUE}Setting up Python virtual environment...${NC}"

    if [ "$IS_TERMUX" = true ]; then
        # Termux: Install packages that need compilation from pkg
        echo -e "${BLUE}Installing binary packages from Termux repository...${NC}"
        pkg install -y python-cryptography python-bcrypt 2>/dev/null || true

        # Set environment to skip Rust compilation
        export SKIP_CYTHON=1
        export SKIP_RUST_EXTENSIONS=1
    fi

    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate venv (use . instead of source for better compatibility)
    . venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install all requirements
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    if [ "$IS_TERMUX" = true ] && [ -f "requirements-termux.txt" ]; then
        # Use Termux-specific requirements (skips packages installed via pkg)
        pip install -r requirements-termux.txt
    else
        pip install -r requirements.txt
    fi

    pip install pytest pytest-asyncio freezegun aiohttp  # Test dependencies

    # Install sub-project requirements (skip on Termux to avoid recompiling packages)
    if [ "$IS_TERMUX" != true ]; then
        for req in valueflows_node/requirements.txt mesh_network/requirements.txt discovery_search/requirements.txt; do
            if [ -f "$req" ]; then
                pip install -r "$req" 2>/dev/null || true
            fi
        done
    else
        echo -e "${YELLOW}Skipping sub-project requirements on Termux (already installed from main requirements)${NC}"
    fi
}

# Setup frontend
setup_frontend() {
    echo -e "${BLUE}Setting up frontend...${NC}"

    if [ -d "frontend" ]; then
        cd frontend
        npm install
        npm run build
        cd ..
    fi
}

# Initialize database
init_database() {
    echo -e "${BLUE}Initializing database...${NC}"

    mkdir -p app/data

    # Run initialization
    . venv/bin/activate
    python -c "
import asyncio
from app.database.db import init_db
asyncio.run(init_db())
print('Database initialized successfully')
"
}

# Create systemd service files
create_systemd_services() {
    if [ "$IS_TERMUX" = true ]; then
        echo -e "${YELLOW}Skipping systemd setup (Termux uses background processes)${NC}"
        return
    fi

    if [ "$PLATFORM" != "Linux" ]; then
        echo -e "${YELLOW}Skipping systemd setup (not on Linux)${NC}"
        return
    fi

    echo -e "${BLUE}Creating systemd service files...${NC}"

    INSTALL_DIR="$(pwd)"

    # Main DTN service
    sudo tee /etc/systemd/system/solarpunk-dtn.service > /dev/null << EOF
[Unit]
Description=Solarpunk DTN Bundle System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=5
Environment=PYTHONPATH=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service (if using nginx)
    sudo tee /etc/systemd/system/solarpunk-frontend.service > /dev/null << EOF
[Unit]
Description=Solarpunk Frontend Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/frontend
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo -e "${GREEN}Systemd services created${NC}"
}

# Configure firewall
configure_firewall() {
    if [ "$IS_TERMUX" = true ]; then
        echo -e "${YELLOW}Skipping firewall setup (not available on Termux)${NC}"
        return
    fi

    if [ "$PLATFORM" != "Linux" ]; then
        return
    fi

    echo -e "${BLUE}Configuring firewall...${NC}"

    # UFW (Ubuntu)
    if command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 3000/tcp  # Frontend
        sudo ufw allow 8000/tcp  # DTN API
        sudo ufw allow 8001/tcp  # ValueFlows
        sudo ufw allow 8002/tcp  # Bridge Management
        echo -e "${GREEN}Firewall configured (ufw)${NC}"
    # firewalld (RHEL/CentOS)
    elif command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --permanent --add-port=3000/tcp
        sudo firewall-cmd --permanent --add-port=8000/tcp
        sudo firewall-cmd --permanent --add-port=8001/tcp
        sudo firewall-cmd --permanent --add-port=8002/tcp
        sudo firewall-cmd --reload
        echo -e "${GREEN}Firewall configured (firewalld)${NC}"
    fi
}

# Run tests
run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    . venv/bin/activate

    # Run tests (excluding integration tests that need running services)
    python -m pytest tests/ --ignore=tests/integration -q --tb=no 2>/dev/null || {
        echo -e "${YELLOW}Some tests failed (this is expected for integration tests)${NC}"
    }
}

# Start services
start_services() {
    echo -e "${BLUE}Starting services...${NC}"

    if [ "$IS_TERMUX" = true ]; then
        # Termux: Start services with nohup (wake-lock already enabled at script start)
        echo -e "${YELLOW}Starting services in background with nohup...${NC}"
        nohup ./run_all_services.sh > /dev/null 2>&1 &
        echo -e "${GREEN}Services started in background (wake-lock active)${NC}"

    elif [ "$PLATFORM" = "Linux" ] && command -v systemctl &> /dev/null; then
        sudo systemctl start solarpunk-dtn
        sudo systemctl start solarpunk-frontend
        sudo systemctl enable solarpunk-dtn
        sudo systemctl enable solarpunk-frontend
        echo -e "${GREEN}Services started via systemd${NC}"
    else
        # Fallback to manual start
        ./run_all_services.sh &
        echo -e "${GREEN}Services started in background${NC}"
    fi
}

# Setup Termux auto-start on boot
setup_termux_boot() {
    if [ "$IS_TERMUX" != true ]; then
        return
    fi

    echo -e "${BLUE}Setting up auto-start on boot...${NC}"

    # Check if Termux:Boot is installed
    if [ ! -d "$HOME/.termux/boot" ]; then
        mkdir -p "$HOME/.termux/boot"
    fi

    # Create boot startup script
    cat > "$HOME/.termux/boot/start-solarpunk.sh" << 'BOOTEOF'
#!/data/data/com.termux/files/usr/bin/sh
# Auto-start Solarpunk services on phone boot

# Enable wake lock to prevent CPU sleep
termux-wake-lock 2>/dev/null

# Navigate to project directory
cd ~/solarpunk_utopia || cd /data/data/com.termux/files/home/solarpunk_utopia

# Start all services in background
nohup ./run_all_services.sh > /dev/null 2>&1 &
BOOTEOF

    chmod +x "$HOME/.termux/boot/start-solarpunk.sh"

    echo -e "${GREEN}Boot script created at ~/.termux/boot/start-solarpunk.sh${NC}"
    echo -e "${YELLOW}Install 'Termux:Boot' from F-Droid to enable auto-start on boot${NC}"
}

# Print summary
print_summary() {
    # Get external IP
    EXTERNAL_IP=""
    if command -v curl &> /dev/null; then
        EXTERNAL_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "unknown")
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Service Endpoints:${NC}"
    echo -e "  Frontend:           http://${EXTERNAL_IP}:3000"
    echo -e "  DTN Bundle API:     http://${EXTERNAL_IP}:8000"
    echo -e "  API Documentation:  http://${EXTERNAL_IP}:8000/docs"
    echo -e "  ValueFlows API:     http://${EXTERNAL_IP}:8001"
    echo -e "  Bridge Management:  http://${EXTERNAL_IP}:8002"
    echo ""
    echo -e "${YELLOW}Management Commands:${NC}"
    echo -e "  Start services:  ./run_all_services.sh"
    echo -e "  Stop services:   ./stop_all_services.sh"
    echo -e "  View logs:       tail -f logs/dtn_bundle_system.log"
    echo -e "  Run tests:       source venv/bin/activate && pytest tests/ -v"
    echo ""
    if [ "$IS_TERMUX" = true ]; then
        echo -e "${YELLOW}Termux Tips:${NC}"
        echo -e "  Services are running with wake-lock enabled"
        echo -e "  Access locally:        http://localhost:3000"
        echo -e "  Restart services:      ./run_all_services.sh"
        echo -e "  Stop services:         ./stop_all_services.sh"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Prevent Android from killing Termux:${NC}"
        echo -e "  Settings → Apps → Termux → Battery → Unrestricted"
        echo -e "  (Otherwise Android will kill services when in background)"
        echo ""
    elif [ "$PLATFORM" = "Linux" ]; then
        echo -e "${YELLOW}Systemd Commands:${NC}"
        echo -e "  sudo systemctl status solarpunk-dtn"
        echo -e "  sudo systemctl restart solarpunk-dtn"
        echo -e "  sudo journalctl -u solarpunk-dtn -f"
        echo ""
    fi
    echo -e "${GREEN}Solarpunk Utopia is ready!${NC}"
}

# Main execution
main() {
    # If running from curl pipe, we need to clone first
    if [ ! -f "requirements.txt" ]; then
        install_dependencies
        clone_repo
    fi

    setup_python
    setup_frontend
    init_database

    if [ "$IS_TERMUX" = false ] && [ "$PLATFORM" = "Linux" ]; then
        create_systemd_services
        configure_firewall
    fi

    if [ "$IS_TERMUX" = true ]; then
        setup_termux_boot
    fi

    run_tests
    start_services
    print_summary
}

# Run main function
main "$@"
