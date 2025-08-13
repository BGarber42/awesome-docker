# Ephemeral Multi-Database Playground

A Docker container that spins up temporary, self-destructing database environments for testing with MySQL, PostgreSQL, and SQLite support.

## 🏷️ Hybrid Tagging Strategy

This project uses a **Hybrid Tagging Strategy** for Docker Hub publishing:

- **`latest` tag** → All-in-one image supporting all DB types, selected via `DB_TYPE` env var at runtime
- **Specific tags** (`postgres`, `mysql`, `sqlite`) → Slimmed single-DB images for minimal size

### Image Variants

| Tag | Description | Size | Use Case |
|-----|-------------|------|----------|
| `latest` | All-in-one with MySQL, PostgreSQL, SQLite | Larger | Development, testing multiple DBs |
| `mysql` | MySQL only | Smaller | Production MySQL testing |
| `postgres` | PostgreSQL only | Smaller | Production PostgreSQL testing |
| `sqlite` | SQLite only | Smallest | Lightweight testing, CI/CD |

## Quick Start

### All-in-One Image (latest)

```bash
# Start with MySQL (default)
docker run -d -p 8080:8080 awesome-docker/ephemeral-multi-db-playground:latest

# Start with PostgreSQL
docker run -d -p 8080:8080 -e DB_TYPE=postgresql awesome-docker/ephemeral-multi-db-playground:latest

# Start with SQLite
docker run -d -p 8080:8080 -e DB_TYPE=sqlite awesome-docker/ephemeral-multi-db-playground:latest

# Start with custom TTL
docker run -d -p 8080:8080 -e TTL=1800 awesome-docker/ephemeral-multi-db-playground:latest
```

### Slim Images

```bash
# MySQL slim image (no DB_TYPE env var needed)
docker run -d -p 8080:8080 awesome-docker/ephemeral-multi-db-playground:mysql

# PostgreSQL slim image
docker run -d -p 8080:8080 awesome-docker/ephemeral-multi-db-playground:postgres

# SQLite slim image
docker run -d -p 8080:8080 awesome-docker/ephemeral-multi-db-playground:sqlite
```

### Docker Compose

```bash
# Start with MySQL (default)
docker compose up -d

# Start with PostgreSQL
DB_TYPE=postgresql docker compose up -d

# Start with custom TTL
TTL=1800 docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | `mysql` | Database type (`mysql`, `postgresql`, `sqlite`) - only used with `latest` tag |
| `TTL` | `86400` | Time to live in seconds (24 hours) |
| `DB_NAME` | `testdb` | Database name |
| `DB_USER` | `testuser` | Database user |
| `DB_PASSWORD` | `testpass` | Database password |

## API Endpoints

### Health & Status
```bash
curl http://localhost:8080/health
curl http://localhost:8080/status
curl http://localhost:8080/info
```

### Reset Database
```bash
curl -X POST http://localhost:8080/reset
```

## Database Schemas

### Sample Tables
- **users** - User management (id, username, email, role, created_at)
- **products** - Product catalog (id, name, category, price, stock, created_at)
- **orders** - Order tracking (id, user_id, product_id, quantity, status, total_amount, created_at)

### Sample Data
- 50+ users with various roles
- 100+ products with categories and prices
- 200+ orders with different statuses

## Ports

| Database | Database Port | API Port |
|----------|---------------|----------|
| MySQL | 3306 | 8080 |
| PostgreSQL | 5432 | 8080 |
| SQLite | - | 8080 |

## Architecture

The playground uses a single-container architecture with embedded database servers:
- **All-in-One Mode**: Contains all database servers, selected at runtime
- **Slim Mode**: Contains only the specified database server
- **API Service**: Python Flask application with database seeding and management
- **Auto-Seeding**: Pre-populated with realistic test data
- **Self-Destruction**: Automatic cleanup after TTL expires

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Start ephemeral database
  run: |
    # Use slim image for faster startup
    docker run -d \
      --name test-db \
      -p 8080:8080 \
      -e TTL=600 \
      awesome-docker/ephemeral-multi-db-playground:sqlite
    
    # Wait for database to be ready
    sleep 10
    
    # Run tests
    npm test
    
    # Cleanup (automatic after TTL)
```

### Local Development
```bash
# Build all variants locally
./build.sh

# Test specific variant
docker run -d -p 8080:8080 awesome-docker/ephemeral-multi-db-playground:mysql
```

## Publishing

The project automatically builds and publishes all image variants to Docker Hub via the monorepo workflow:

```bash
# Manual build commands
docker build -t awesome-docker/ephemeral-multi-db-playground:latest .
docker build --build-arg DB_TYPE=postgres -t awesome-docker/ephemeral-multi-db-playground:postgres .
docker build --build-arg DB_TYPE=mysql -t awesome-docker/ephemeral-multi-db-playground:mysql .
docker build --build-arg DB_TYPE=sqlite -t awesome-docker/ephemeral-multi-db-playground:sqlite .
```

## Features

- **Hybrid Tagging**: All-in-one and slim image variants
- **Multi-Database Support**: MySQL, PostgreSQL, SQLite
- **Auto-Seeding**: Pre-populated with realistic test data
- **Self-Destruction**: Automatic cleanup after TTL expires
- **Reset Endpoint**: Clear and reseed database via HTTP API
- **CI/CD Friendly**: Perfect for automated testing
- **Health Monitoring**: Built-in health checks and status reporting
- **Embedded Databases**: No external dependencies required
