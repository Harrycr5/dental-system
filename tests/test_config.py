import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", db_password="x")


def test_production_requires_db_password():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", secret_key="a" * 40)


def test_production_ok_with_secrets():
    s = Settings(_env_file=None, environment="production", secret_key="a" * 40, db_password="pw")
    assert s.environment == "production"


def test_database_url_escapes_special_chars():
    s = Settings(_env_file=None, db_password="p@ss:/word")
    assert "p%40ss%3A%2Fword" in s.database_url
    assert s.database_url.startswith("postgresql+psycopg://")


def test_redis_urls_use_distinct_dbs_and_password():
    s = Settings(_env_file=None, redis_password="a b", redis_host="redis")
    assert s.redis_url == "redis://:a%20b@redis:6379/0"
    assert s.celery_broker_url.endswith("/1")


def test_invalid_timezone_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, timezone="Mars/Olympus")
