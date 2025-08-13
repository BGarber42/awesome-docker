#!/bin/bash
set -e

# Set default values
DB_TYPE=${DB_TYPE:-mysql}
TTL=${TTL:-86400}
DB_NAME=${DB_NAME:-testdb}
DB_USER=${DB_USER:-testuser}
DB_PASSWORD=${DB_PASSWORD:-testpass}

# Detect if we're running in slim mode (baked-in database type)
# Check which database servers are available
SLIM_MODE=false
BAKED_DB_TYPE=""

if command -v mysql &> /dev/null && ! command -v postgres &> /dev/null; then
    SLIM_MODE=true
    BAKED_DB_TYPE="mysql"
elif command -v postgres &> /dev/null && ! command -v mysql &> /dev/null; then
    SLIM_MODE=true
    BAKED_DB_TYPE="postgresql"
elif ! command -v mysql &> /dev/null && ! command -v postgres &> /dev/null; then
    SLIM_MODE=true
    BAKED_DB_TYPE="sqlite"
fi

# In slim mode, override DB_TYPE with the baked-in type
if [ "$SLIM_MODE" = true ]; then
    DB_TYPE=$BAKED_DB_TYPE
    echo "Running in slim mode with baked-in database: $DB_TYPE"
fi

# Export environment variables for Python processes
export DB_TYPE
export TTL
export DB_NAME
export DB_USER
export DB_PASSWORD

echo "Starting ephemeral database playground..."
echo "Database Type: $DB_TYPE"
echo "TTL: $TTL seconds"
echo "Database: $DB_NAME"
echo "Mode: $([ "$SLIM_MODE" = true ] && echo "Slim" || echo "All-in-one")"

# Function to start database server
start_database() {
    case $DB_TYPE in
        mysql)
            echo "Starting MySQL..."
            service mysql start
            
            # Wait for MySQL to be ready
            for i in {1..30}; do
                if mysql -e "SELECT 1" >/dev/null 2>&1; then
                    break
                fi
                echo "Waiting for MySQL to be ready... ($i/30)"
                sleep 2
            done
            
            mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
            mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';"
            mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';"
            mysql -e "FLUSH PRIVILEGES;"
            echo "MySQL setup completed"
            ;;
        postgresql)
            echo "Starting PostgreSQL..."
            service postgresql start
            
            # Wait for PostgreSQL to be ready
            for i in {1..30}; do
                if sudo -u postgres psql -c "SELECT 1" >/dev/null 2>&1; then
                    break
                fi
                echo "Waiting for PostgreSQL to be ready... ($i/30)"
                sleep 2
            done
            
            sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || true
            sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true
            sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" || true
            echo "PostgreSQL setup completed"
            ;;
        sqlite)
            echo "Using SQLite..."
            mkdir -p /app/data
            echo "SQLite setup completed"
            ;;
        *)
            echo "Unsupported database type: $DB_TYPE"
            exit 1
            ;;
    esac
}

# Function to seed database
seed_database() {
    echo "Seeding database with sample data..."
    python /app/scripts/seed_database.py
    echo "Database seeding completed"
}

# Function to start API server
start_api() {
    echo "Starting API server..."
    python /app/app/main.py &
    API_PID=$!
    echo "API server started with PID: $API_PID"
}

# Function to start TTL timer
start_ttl_timer() {
    echo "Starting TTL timer for $TTL seconds..."
    sleep $TTL
    echo "TTL expired. Shutting down..."
    kill $API_PID 2>/dev/null || true
    exit 0
}

# Main execution
echo "Setting up database..."
start_database

echo "Seeding database..."
seed_database

echo "Starting API server..."
start_api

echo "Starting TTL timer..."
start_ttl_timer
