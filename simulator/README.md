# quarry-sim

Simulates the quarry and crushing plant and writes the raw data each source system would deliver. Standalone: runs inside the Industrial Data Platform repo or on any machine with Python 3.11+ or Docker.

Data design: [`docs/phase-01-quarry/data-requirements.md`](../docs/phase-01-quarry/data-requirements.md).

## Run

```bash
# Python (from this folder)
PYTHONPATH=src python -m quarry_sim --start-date 2026-11-02 --days 7 --output ./output

# Docker, standalone
docker build -t quarry-sim .
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD/output:/data" quarry-sim --start-date 2026-11-02

# Docker Compose (this folder's compose.yml). Writes to ../data/raw/ by default
mkdir -p ../data/raw   # create it first, or Docker creates it owned by root
docker compose run --rm simulator --start-date 2026-11-02 --days 7

# On another machine, choose where the data goes
SIM_OUTPUT_DIR=./output docker compose run --rm simulator --start-date 2026-11-02
```

| Option | Default | Meaning |
|---|---|---|
| `--start-date` | required | First simulated day (YYYY-MM-DD) |
| `--days` | 7 | Days to simulate |
| `--seed` | 42 | Same seed + same dates = identical output |
| `--output` | `$QUARRY_SIM_OUTPUT` or `./output` | Output directory |

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
