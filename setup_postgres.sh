#!/bin/bash

# ============================================================
# Fint Backend - PostgreSQL Local Setup Script
# ============================================================
# This script sets up PostgreSQL for local/remote development
# Run with: ./setup_postgres.sh
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       Fint Backend - PostgreSQL Setup Script${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Prompt user for configuration
echo -e "${BLUE}Please enter database configuration:${NC}"
echo ""

read -p "Database name [fint_db]: " input_db_name
DB_NAME="${input_db_name:-fint_db}"

read -p "Database user [fint_user]: " input_db_user
DB_USER="${input_db_user:-fint_user}"

read -s -p "Database password [fint_password_123]: " input_db_password
echo ""
DB_PASSWORD="${input_db_password:-fint_password_123}"

read -p "Database host [localhost]: " input_db_host
DB_HOST="${input_db_host:-localhost}"

read -p "Database port [5432]: " input_db_port
DB_PORT="${input_db_port:-5432}"

read -p "Allow remote connections (for TablePlus, etc)? [y/N]: " allow_remote
ALLOW_REMOTE="${allow_remote:-n}"

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Database: ${YELLOW}$DB_NAME${NC}"
echo -e "  User:     ${YELLOW}$DB_USER${NC}"
echo -e "  Host:     ${YELLOW}$DB_HOST${NC}"
echo -e "  Port:     ${YELLOW}$DB_PORT${NC}"
echo -e "  Remote:   ${YELLOW}$ALLOW_REMOTE${NC}"
echo ""

# Function to check if PostgreSQL is installed
check_postgres_installed() {
    if command -v psql &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL client is installed${NC}"
        return 0
    else
        echo -e "${RED}✗ PostgreSQL is not installed${NC}"
        return 1
    fi
}

# Function to check if PostgreSQL service is running
check_postgres_running() {
    if pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is running on $DB_HOST:$DB_PORT${NC}"
        return 0
    else
        echo -e "${RED}✗ PostgreSQL is not running${NC}"
        return 1
    fi
}

# Function to install PostgreSQL
install_postgres() {
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Debian/Ubuntu
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        # Fedora/RHEL
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y postgresql-server postgresql-contrib
            sudo postgresql-setup --initdb
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        # Arch Linux
        elif command -v pacman &> /dev/null; then
            sudo pacman -S postgresql
            sudo -u postgres initdb -D /var/lib/postgres/data
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS with Homebrew
        if command -v brew &> /dev/null; then
            brew install postgresql@14
            brew services start postgresql@14
        else
            echo -e "${RED}Please install Homebrew first: https://brew.sh${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Unsupported OS. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ PostgreSQL installed successfully${NC}"
}

# Function to create database and user
setup_database() {
    echo ""
    echo -e "${BLUE}Setting up database...${NC}"
    
    # Create user if not exists
    echo -e "${YELLOW}Creating database user...${NC}"
    sudo -u postgres psql -c "DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
            CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        END IF;
    END
    \$\$;" 2>/dev/null || {
        # For macOS where sudo -u postgres might not work
        psql -U postgres -c "DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
                CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
            END IF;
        END
        \$\$;" 2>/dev/null || true
    }
    
    # Update password in case user already exists
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || \
        psql -U postgres -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || true
    
    echo -e "${GREEN}✓ User created or updated${NC}"
    
    # Create database if not exists
    echo -e "${YELLOW}Creating database...${NC}"
    sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
        sudo -u postgres createdb -O $DB_USER $DB_NAME 2>/dev/null || \
        createdb -U postgres -O $DB_USER $DB_NAME 2>/dev/null || true
    echo -e "${GREEN}✓ Database created or already exists${NC}"
    
    # Grant privileges
    echo -e "${YELLOW}Granting privileges...${NC}"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || \
        psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
    echo -e "${GREEN}✓ Privileges granted${NC}"
}

# Function to configure remote access (for TablePlus, DBeaver, etc.)
configure_remote_access() {
    if [[ ! "$ALLOW_REMOTE" =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    echo ""
    echo -e "${BLUE}Configuring remote access...${NC}"
    
    # Find PostgreSQL config directory
    PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
    PG_CONF_DIR=""
    
    # Check common locations
    if [ -d "/etc/postgresql/$PG_VERSION/main" ]; then
        PG_CONF_DIR="/etc/postgresql/$PG_VERSION/main"
    elif [ -d "/var/lib/pgsql/$PG_VERSION/data" ]; then
        PG_CONF_DIR="/var/lib/pgsql/$PG_VERSION/data"
    elif [ -d "/var/lib/pgsql/data" ]; then
        PG_CONF_DIR="/var/lib/pgsql/data"
    elif [ -d "/usr/local/var/postgres" ]; then
        PG_CONF_DIR="/usr/local/var/postgres"  # macOS Homebrew
    elif [ -d "/opt/homebrew/var/postgres" ]; then
        PG_CONF_DIR="/opt/homebrew/var/postgres"  # macOS M1 Homebrew
    fi
    
    if [ -z "$PG_CONF_DIR" ]; then
        echo -e "${YELLOW}⚠ Could not find PostgreSQL config directory${NC}"
        echo -e "${YELLOW}  Please manually configure remote access:${NC}"
        echo ""
        echo -e "  1. Edit postgresql.conf and set: ${YELLOW}listen_addresses = '*'${NC}"
        echo -e "  2. Edit pg_hba.conf and add: ${YELLOW}host all all 0.0.0.0/0 md5${NC}"
        echo -e "  3. Restart PostgreSQL: ${YELLOW}sudo systemctl restart postgresql${NC}"
        echo -e "  4. Open firewall port: ${YELLOW}sudo ufw allow 5432/tcp${NC}"
        return 0
    fi
    
    echo -e "  Config directory: ${YELLOW}$PG_CONF_DIR${NC}"
    
    # Backup config files
    echo -e "${YELLOW}Backing up config files...${NC}"
    sudo cp "$PG_CONF_DIR/postgresql.conf" "$PG_CONF_DIR/postgresql.conf.backup" 2>/dev/null || true
    sudo cp "$PG_CONF_DIR/pg_hba.conf" "$PG_CONF_DIR/pg_hba.conf.backup" 2>/dev/null || true
    
    # Update postgresql.conf to listen on all interfaces
    echo -e "${YELLOW}Updating postgresql.conf...${NC}"
    if grep -q "^listen_addresses" "$PG_CONF_DIR/postgresql.conf" 2>/dev/null; then
        sudo sed -i "s/^listen_addresses.*/listen_addresses = '*'/" "$PG_CONF_DIR/postgresql.conf"
    elif grep -q "^#listen_addresses" "$PG_CONF_DIR/postgresql.conf" 2>/dev/null; then
        sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" "$PG_CONF_DIR/postgresql.conf"
    else
        echo "listen_addresses = '*'" | sudo tee -a "$PG_CONF_DIR/postgresql.conf" > /dev/null
    fi
    echo -e "${GREEN}✓ postgresql.conf updated (listen_addresses = '*')${NC}"
    
    # Update pg_hba.conf to allow remote connections with password
    echo -e "${YELLOW}Updating pg_hba.conf...${NC}"
    
    # Check if remote access line already exists
    if ! grep -q "host.*all.*all.*0.0.0.0/0.*md5" "$PG_CONF_DIR/pg_hba.conf" 2>/dev/null; then
        # Add IPv4 remote access
        echo "# Allow remote connections (added by setup script)" | sudo tee -a "$PG_CONF_DIR/pg_hba.conf" > /dev/null
        echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a "$PG_CONF_DIR/pg_hba.conf" > /dev/null
        # Add IPv6 remote access
        echo "host    all             all             ::/0                    md5" | sudo tee -a "$PG_CONF_DIR/pg_hba.conf" > /dev/null
    fi
    echo -e "${GREEN}✓ pg_hba.conf updated (remote access enabled)${NC}"
    
    # Restart PostgreSQL
    echo -e "${YELLOW}Restarting PostgreSQL...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl restart postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services restart postgresql@$PG_VERSION 2>/dev/null || brew services restart postgresql
    fi
    echo -e "${GREEN}✓ PostgreSQL restarted${NC}"
    
    # Configure firewall (Linux only)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "${YELLOW}Configuring firewall...${NC}"
        if command -v ufw &> /dev/null; then
            sudo ufw allow $DB_PORT/tcp 2>/dev/null || true
            echo -e "${GREEN}✓ UFW firewall rule added for port $DB_PORT${NC}"
        elif command -v firewall-cmd &> /dev/null; then
            sudo firewall-cmd --permanent --add-port=$DB_PORT/tcp 2>/dev/null || true
            sudo firewall-cmd --reload 2>/dev/null || true
            echo -e "${GREEN}✓ firewalld rule added for port $DB_PORT${NC}"
        else
            echo -e "${YELLOW}⚠ No firewall detected. Make sure port $DB_PORT is open.${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}       Remote Access Configured!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "You can now connect from TablePlus/DBeaver using:"
    echo -e "  Host:     ${YELLOW}$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'your-server-ip')${NC}"
    echo -e "  Port:     ${YELLOW}$DB_PORT${NC}"
    echo -e "  Database: ${YELLOW}$DB_NAME${NC}"
    echo -e "  User:     ${YELLOW}$DB_USER${NC}"
    echo -e "  Password: ${YELLOW}(the password you entered)${NC}"
    echo ""
}

# Function to create .env file
create_env_file() {
    echo ""
    echo -e "${BLUE}Creating .env file...${NC}"
    
    ENV_FILE=".env"
    DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    if [ -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠ .env file already exists. Backing up to .env.backup${NC}"
        cp "$ENV_FILE" ".env.backup"
    fi
    
    cat > "$ENV_FILE" << EOF
# Database Configuration
DATABASE_URL=$DATABASE_URL

# Django Settings
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || echo "change-this-secret-key-in-production")
DEBUG=True

# CORS Settings (comma-separated origins)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://fint.ngthav.xyz

# Email Configuration (Zoho Mail SSL)
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@fint.app

# Frontend URL (for password reset links)
FRONTEND_URL=http://fint.ngthav.xyz
EOF
    
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "  DATABASE_URL: ${YELLOW}$DATABASE_URL${NC}"
}

# Function to run Django migrations
run_migrations() {
    echo ""
    echo -e "${BLUE}Running Django migrations...${NC}"
    
    if [ -f "manage.py" ]; then
        python3 manage.py migrate
        echo -e "${GREEN}✓ Migrations completed${NC}"
    else
        echo -e "${RED}✗ manage.py not found. Run this script from the project root.${NC}"
        exit 1
    fi
}

# Function to seed default data
seed_data() {
    echo ""
    echo -e "${BLUE}Seeding default data...${NC}"
    
    if [ -f "seed_data.py" ]; then
        python3 seed_data.py
        echo -e "${GREEN}✓ Default data seeded${NC}"
    else
        echo -e "${YELLOW}⚠ seed_data.py not found. Skipping data seeding.${NC}"
    fi
}

# Function to verify setup
verify_setup() {
    echo ""
    echo -e "${BLUE}Verifying setup...${NC}"
    
    # Test database connection
    python3 << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fint_backend.settings')
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("\033[0;32m✓ Database connection successful\033[0m")
except Exception as e:
    print(f"\033[0;31m✗ Database connection failed: {e}\033[0m")
    exit(1)
EOF
}

# Main execution
main() {
    echo ""
    
    # Check if PostgreSQL is installed
    if ! check_postgres_installed; then
        read -p "Would you like to install PostgreSQL? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_postgres
        else
            echo -e "${RED}PostgreSQL is required. Exiting.${NC}"
            exit 1
        fi
    fi
    
    # Check if PostgreSQL is running
    if ! check_postgres_running; then
        echo -e "${YELLOW}Attempting to start PostgreSQL...${NC}"
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start postgresql
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start postgresql@14 2>/dev/null || brew services start postgresql
        fi
        sleep 2
        if ! check_postgres_running; then
            echo -e "${RED}Failed to start PostgreSQL. Please start it manually.${NC}"
            exit 1
        fi
    fi
    
    # Setup database
    setup_database
    
    # Configure remote access if requested
    configure_remote_access
    
    # Create .env file
    create_env_file
    
    # Check for virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        echo ""
        echo -e "${YELLOW}⚠ Virtual environment not detected.${NC}"
        echo -e "${YELLOW}  Consider activating your venv before running migrations.${NC}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # Run migrations
    run_migrations
    
    # Seed data
    seed_data
    
    # Verify setup
    verify_setup
    
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}       PostgreSQL Setup Complete!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "You can now start the server with:"
    echo -e "  ${YELLOW}python3 manage.py runserver 0.0.0.0:5000${NC}"
    echo ""
    echo -e "Or for production:"
    echo -e "  ${YELLOW}./start.sh production${NC}"
    echo ""
}

# Run main function
main
