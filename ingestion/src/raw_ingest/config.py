"""Database connection settings, read from environment variables."""

import os
from dataclasses import dataclass, field

REQUIRED = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")


class ConfigError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    user: str
    dbname: str
    password: str = field(repr=False)  # never printed in logs or tracebacks


def load_db_config(env: dict[str, str] | None = None) -> DbConfig:
    """Build a DbConfig, reporting every problem at once instead of the first one."""
    env = os.environ if env is None else env
    errors = [f"missing environment variable {name}" for name in REQUIRED if not env.get(name)]

    port_text = env.get("POSTGRES_PORT", "5432")
    try:
        port = int(port_text)
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        errors.append(f"POSTGRES_PORT must be a number between 1 and 65535, got {port_text!r}")

    if errors:
        raise ConfigError(errors)

    return DbConfig(
        host=env.get("POSTGRES_HOST", "localhost"),
        port=port,
        user=env["POSTGRES_USER"],
        dbname=env["POSTGRES_DB"],
        password=env["POSTGRES_PASSWORD"],
    )
