from datetime import UTC, datetime

import pytest

from app.core.timeutils import ensure_aware, to_local


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        ensure_aware(datetime(2026, 1, 1, 10, 0))


def test_to_local_lima_is_utc_minus_5():
    local = to_local(datetime(2026, 1, 1, 15, 0, tzinfo=UTC))
    assert local.hour == 10
