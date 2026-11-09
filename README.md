# Industrial Data Platform

Industrial Data Platform is a Data Engineering learning project that simulates the data architecture of a cement manufacturing operation.

The project will evolve progressively from raw industrial data generation to ingestion, transformation, data quality, orchestration, streaming and cloud deployment.

## Current Phase

### Phase 01 — Quarry & Limestone Crushing

From the quarry bench to the crushed-limestone stockpile:

- Drilling and blasting
- Loading and haulage (excavators, loaders, haul trucks with on-board payload sensors)
- Primary crushing (hopper, crusher, belt scale)
- Online quality measurement (cross-belt analyzer, laboratory validation)
- Equipment maintenance

A Python simulator acts as the plant. It produces the data each source system would deliver:

| Source system | Delivers | Format |
|---|---|---|
| Planning spreadsheet | Drilling & blasting | Excel file (weekly) |
| Fleet management system (FMS) | Equipment telemetry & sensor events | REST API |
| Maintenance system (CMMS) | Assets, work orders, spare parts | PostgreSQL database |
| Laboratory (LIMS) | Analyzer validation samples | CSV/JSON (daily, late-arriving) |
| Plant historian (SCADA) | Crusher, belt scale and analyzer readings | CSV (every minute) |

Full data requirements: [`docs/phase-01-quarry/data-requirements.md`](docs/phase-01-quarry/data-requirements.md).

## Architecture

```text
Simulated source systems (files, REST API, database)
        ↓
Bronze — raw data, as delivered
        ↓
PostgreSQL
        ↓
Silver — cleaned and conformed (staging)
        ↓
Gold — dimensional model and KPIs (core)
        ↓
Analytics
```

## Quick Start

Requires Docker with Docker Compose.

```bash
cp .env.example .env     # then set your own passwords
docker compose up -d
```

| Service | URL |
|---|---|
| PostgreSQL | `localhost:5432` |
| pgAdmin | http://localhost:5050 |
| Jupyter | http://localhost:8888 |

In pgAdmin, register the server with host `postgres` and port `5432`. Containers reach each other by service name on the Compose network, so use `postgres`, not `localhost`.

## Status

- [x] Local PostgreSQL + pgAdmin environment with persistent storage
- [ ] Quarry simulator (in progress)
- [ ] Ingestion into PostgreSQL
- [ ] Silver and Gold models
