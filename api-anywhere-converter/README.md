# API Anywhere Converter

Auto-generate REST and GraphQL APIs from databases and CSV files with zero configuration.

## Features

- **Multi-Source Support**: MySQL, PostgreSQL, SQLite with automatic schema detection
- **CSV Processing**: Upload CSV files and instantly create queryable APIs
- **REST & GraphQL**: Auto-generated CRUD operations and GraphQL playground
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`
- **Production Ready**: Health checks, error handling, pagination, connection pooling

## Quick Start

```bash
# Start the container
docker compose up -d

# Check health
curl http://localhost:8000/health

# Access API documentation
open http://localhost:8000/docs
```

## Usage

### Database Integration

```bash
# Connect to a database
curl -X POST -H "Content-Type: application/json" \
  -d '{"db_url":"sqlite:///path/to/database.db"}' \
  http://localhost:8000/connect

# List all tables
curl "http://localhost:8000/tables?db_url=sqlite:///path/to/database.db"

# Get data from a table
curl "http://localhost:8000/api/users?db_url=sqlite:///path/to/database.db"

# Create a new record
curl -X POST -H "Content-Type: application/json" \
  -d '{"data":{"name":"John Doe","email":"john@example.com","age":30}}' \
  "http://localhost:8000/api/users?db_url=sqlite:///path/to/database.db"

# Update a record
curl -X PUT -H "Content-Type: application/json" \
  -d '{"data":{"name":"John Updated","email":"john.updated@example.com"}}' \
  "http://localhost:8000/api/users/1?db_url=sqlite:///path/to/database.db"

# Delete a record
curl -X DELETE "http://localhost:8000/api/users/1?db_url=sqlite:///path/to/database.db"
```

### CSV Processing

```bash
# Upload a CSV file
curl -X POST -F "file=@data.csv" -F "table_name=my_data" \
  http://localhost:8000/upload

# Get data from uploaded CSV
curl http://localhost:8000/api/my_data

# Create a new record in CSV data
curl -X POST -H "Content-Type: application/json" \
  -d '{"data":{"name":"New Record","value":123}}' \
  http://localhost:8000/api/my_data

# Update a record in CSV data
curl -X PUT -H "Content-Type: application/json" \
  -d '{"data":{"name":"Updated Record","value":456}}' \
  http://localhost:8000/api/my_data/1

# Delete a record from CSV data
curl -X DELETE http://localhost:8000/api/my_data/1
```

## API Endpoints

### Core Endpoints
- `GET /health` - Service health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

### Database Operations
- `POST /connect` - Connect to a database
- `GET /tables` - List all tables (CSV + Database)
- `GET /api/{table_name}` - Get table data with pagination
- `GET /api/{table_name}/{record_id}` - Get specific record
- `POST /api/{table_name}` - Create new record
- `PUT /api/{table_name}/{record_id}` - Update record
- `DELETE /api/{table_name}/{record_id}` - Delete record

### File Operations
- `POST /upload` - Upload CSV file and create virtual table

### GraphQL
- `POST /graphql` - GraphQL endpoint with playground

## Supported Database Types

### SQLite
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"db_url":"sqlite:///path/to/database.db"}' \
  http://localhost:8000/connect
```

### PostgreSQL
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"db_url":"postgresql://user:password@localhost:5432/dbname"}' \
  http://localhost:8000/connect
```

### MySQL
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"db_url":"mysql://user:password@localhost:3306/dbname"}' \
  http://localhost:8000/connect
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_URL` | Default database connection URL | None |
| `CORS_ORIGIN` | CORS allowed origins | `*` |

## Docker Compose

```yaml
services:
  api-converter:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_URL=${DB_URL}
      - CORS_ORIGIN=*
    volumes:
      - csv_data:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  csv_data:
```

### Using with Default Database

When you set the `DB_URL` environment variable, you can use the API without specifying the database URL in each request:

```bash
# Start with default database
export DB_URL="sqlite:///path/to/database.db"
docker compose up -d

# Now you can use the API without db_url parameter
curl http://localhost:8000/tables
curl http://localhost:8000/api/users
```

### Using with Multiple Databases

You can still override the default database by providing a `db_url` parameter:

```bash
# Use default database
curl http://localhost:8000/api/users

# Override with different database
curl "http://localhost:8000/api/users?db_url=postgresql://user:pass@localhost:5432/otherdb"
```

## License

MIT License - see LICENSE file for details.
