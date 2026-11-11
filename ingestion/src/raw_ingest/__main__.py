"""Command-line entry point: python -m raw_ingest"""

import logging
import sys

import psycopg

from raw_ingest.config import ConfigError, load_db_config

log = logging.getLogger("raw_ingest")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    try:
        config = load_db_config()
    except ConfigError as exc:
        for error in exc.errors:
            log.error("Config: %s", error)
        return 1

    log.info("Connecting to %s:%s/%s as %s", config.host, config.port, config.dbname, config.user)
    try:
        with psycopg.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            dbname=config.dbname,
            connect_timeout=5,
        ) as conn:
            (version,) = conn.execute("SELECT version()").fetchone()
    except psycopg.OperationalError as exc:
        log.error("Cannot connect to PostgreSQL: %s", exc)
        return 1

    log.info("Connected: %s", version)
    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
