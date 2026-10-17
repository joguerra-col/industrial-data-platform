# Industrial Data Platform

Industrial Data Platform is a Data Engineering learning project that simulates the data architecture of a cement manufacturing operation.

The project will evolve progressively from raw industrial data generation to ingestion, transformation, data quality, orchestration, streaming and cloud deployment.

## Current Phase

### Phase 01 — Quarry & Limestone Crushing

The first phase models the limestone extraction process:

- Quarry extraction
- Drilling and blasting
- Heavy equipment operation
- Loading and haulage
- Fuel and consumables
- Weighing
- Material quality
- Limestone crushing
- Inventory management

## Initial Architecture

```text
Industrial Process
        ↓
Python Simulator
        ↓
Raw Data
        ↓
PostgreSQL
        ↓
Staging
        ↓
Core Data Model
        ↓
Analytics
