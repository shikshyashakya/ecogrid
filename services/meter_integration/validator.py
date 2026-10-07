"""Ingestion validator (Member 2): rejects duplicate and invalid readings.
Rejected readings go to a 'dead-letter' list for inspection instead of being lost."""
from datetime import datetime

from contracts.events import MeterReading

MAX_KWH_PER_READING = 10.0


class ReadingValidator:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()
        self.dead_letter: list[tuple[MeterReading, str]] = []

    def check(self, r: MeterReading) -> str | None:
        """Return a rejection reason, or None if the reading is valid."""
        try:
            datetime.fromisoformat(r.timestamp)
        except ValueError:
            return "bad timestamp"
        if not 0 <= r.kwh <= MAX_KWH_PER_READING:
            return "kWh out of range"
        if (r.meter_id, r.timestamp) in self._seen:
            return "duplicate"
        return None

    def process(self, readings: list[MeterReading]) -> list[MeterReading]:
        accepted = []
        for r in readings:
            reason = self.check(r)
            if reason:
                self.dead_letter.append((r, reason))
            else:
                self._seen.add((r.meter_id, r.timestamp))
                accepted.append(r)
        return accepted


def total_kwh(readings: list[MeterReading], meter_id: str) -> float:
    """Energy for one meter over a set of readings (used to verify delivery)."""
    return round(sum(r.kwh for r in readings if r.meter_id == meter_id), 3)
