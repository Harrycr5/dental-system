"""Convención: se almacena y transmite UTC (timestamptz); America/Lima solo para presentación."""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

LIMA = ZoneInfo("America/Lima")


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Se requiere una fecha/hora con zona horaria (ISO 8601 con offset)")
    return dt


def to_local(dt: datetime, tz: ZoneInfo = LIMA) -> datetime:
    return ensure_aware(dt).astimezone(tz)
