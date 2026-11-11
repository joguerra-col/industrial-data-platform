import pytest

from raw_ingest.config import ConfigError, DbConfig, load_db_config

VALID_ENV = {
    "POSTGRES_HOST": "db.example",
    "POSTGRES_PORT": "6543",
    "POSTGRES_USER": "loader",
    "POSTGRES_PASSWORD": "s3cret",
    "POSTGRES_DB": "industrial_data",
}


def test_valid_env_builds_config():
    config = load_db_config(VALID_ENV)

    assert config == DbConfig(
        host="db.example", port=6543, user="loader", dbname="industrial_data", password="s3cret"
    )


def test_host_and_port_have_defaults():
    env = {k: v for k, v in VALID_ENV.items() if k not in ("POSTGRES_HOST", "POSTGRES_PORT")}

    config = load_db_config(env)

    assert (config.host, config.port) == ("localhost", 5432)


@pytest.mark.parametrize("name", ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"])
def test_missing_required_variable_is_reported(name):
    env = {k: v for k, v in VALID_ENV.items() if k != name}

    with pytest.raises(ConfigError) as exc_info:
        load_db_config(env)

    assert any(name in error for error in exc_info.value.errors)


def test_empty_value_counts_as_missing():
    with pytest.raises(ConfigError, match="POSTGRES_PASSWORD"):
        load_db_config({**VALID_ENV, "POSTGRES_PASSWORD": ""})


@pytest.mark.parametrize("port", ["abc", "0", "65536", ""])
def test_invalid_port_is_rejected(port):
    with pytest.raises(ConfigError, match="POSTGRES_PORT"):
        load_db_config({**VALID_ENV, "POSTGRES_PORT": port})


def test_all_errors_are_reported_together():
    with pytest.raises(ConfigError) as exc_info:
        load_db_config({"POSTGRES_PORT": "abc"})

    assert len(exc_info.value.errors) == 4  # 3 missing variables + bad port


def test_password_is_hidden_from_repr():
    config = load_db_config(VALID_ENV)

    assert "s3cret" not in repr(config)
