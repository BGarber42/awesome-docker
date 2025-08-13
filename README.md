# Awesome Docker

A collection of production-ready Docker projects for common development and ops scenarios. Each lives in its own directory with a dedicated README and compose setup.

## Repository structure

- api-anywhere-converter — Generate REST APIs from DBs/CSV using a simple config; Python FastAPI container
- browserless-debug-ai — Headless Chromium with debugging endpoints and AI-assisted traces
- ephemeral-multi-db-playground — Disposable Postgres/MySQL/Redis instances for tests and demos
- single-image-tsdb-grafana — QuestDB + Grafana in one container with sample metrics

## Quick start

Navigate to a project and follow its README
```bash
cd single-image-tsdb-grafana
docker compose up -d
```

## Requirements
- Docker 20.10+
- Docker Compose 2+

## Contributing
PRs welcome. Keep each project self-contained and documented.

## License
MIT (see LICENSE)
