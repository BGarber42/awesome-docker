# Single-Image TSDB + Grafana

A ready-to-run Docker setup bundling QuestDB (time-series database) and Grafana with a prebuilt dashboard and datasource.

## Quick start

```bash
# Start (Docker Compose)
docker compose up -d

# Stop
docker compose down
```

- Grafana: http://localhost:3000 (default admin/admin)
- QuestDB REST/Web Console: http://localhost:9000
- QuestDB PostgreSQL: localhost:8812
- QuestDB ILP (HTTP/TCP): localhost:9009

## What you get
- QuestDB 9.0.1 (SQL + REST + PG wire + ILP)
- Grafana 12.1.0 with a provisioned PostgreSQL datasource and a "System Metrics" dashboard
- Optional sample metrics generator (CPU, memory, disk, network, application)

## Configuration (env)
Set in `docker-compose.yml` and override via your shell env or `.env` file.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ADMIN_USER` | `admin` | Grafana admin user |
| `ADMIN_PASSWORD` | `admin` | Grafana admin password |
| `SAMPLE_METRICS` | `true` | Enable sample metrics long-running service |
| `SAMPLE_INTERVAL` | `15` | Seconds between sample metric batches |

Notes
- To disable sample data generation, set `SAMPLE_METRICS=false` and recreate the container.
- Historical data persists in volumes even after disabling the generator.

## Data persistence
Compose mounts named volumes by default:
- QuestDB: `questdb_data` → `/var/lib/questdb`
- Grafana: `grafana_data` → `/var/lib/grafana`

## Usage examples

### Query data (QuestDB REST)
```bash
# Latest timestamp seen per table
curl -s "http://localhost:9000/exec?query=SELECT%20max(timestamp)%20FROM%20cpu_usage"
```

### Write data (QuestDB ILP/HTTP)
```bash
# One CPU sample (ns timestamp)
TS=$(python - <<'PY'
import time; print(time.time_ns())
PY
)
curl -s -X POST http://localhost:9000/write \
  -H "Content-Type: text/plain" \
  -d "cpu_usage,host=serverX value=75.2 $TS"
```

### Grafana API
```bash
# Health
curl -s http://localhost:3000/api/health

# Datasources (basic auth)
curl -s -u admin:admin http://localhost:3000/api/datasources

# Provisioned dashboard by UID
curl -s -u admin:admin http://localhost:3000/api/dashboards/uid/system-metrics
```

## Dashboard queries (PostgreSQL datasource)
- CPU
  ```sql
  SELECT $__time(timestamp), host AS metric, value
  FROM cpu_usage
  WHERE $__timeFilter(timestamp)
  ORDER BY 1
  ```
- Memory
  ```sql
  SELECT $__time(timestamp), host AS metric, value
  FROM memory_usage
  WHERE $__timeFilter(timestamp)
  ORDER BY 1
  ```
- Disk
  ```sql
  SELECT $__time(timestamp), (host || '/' || device) AS metric, value
  FROM disk_usage
  WHERE $__timeFilter(timestamp)
  ORDER BY 1
  ```
- Network (two targets: bytes_in / bytes_out)
  ```sql
  SELECT $__time(timestamp), (host || '/' || interface) AS metric, bytes_in AS value
  FROM network_traffic
  WHERE $__timeFilter(timestamp)
  ORDER BY 1
  ```
- Application (response time)
  ```sql
  SELECT $__time(timestamp), (service || ' ' || endpoint) AS metric, response_time AS value
  FROM application_metrics
  WHERE $__timeFilter(timestamp)
  ORDER BY 1
  ```

## Troubleshooting
- Service logs inside the container:
  ```bash
  docker exec <container> tail -n 100 /app/logs/questdb.log
  docker exec <container> tail -n 100 /app/logs/grafana.log
  ```
- Common issues
  - No data in dashboard: sample metrics disabled or insufficient time range
  - Credentials error in Grafana datasource: ensure datasource points to `localhost:8812` and user `admin`
  - Windows/PowerShell: pipes are interpreted by PowerShell; to run Linux pipelines, prefer:
    ```bash
    wsl bash -lc "docker logs <container> | grep error | tail -n 20"
    ```
