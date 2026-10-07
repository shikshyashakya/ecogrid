"""Smart-meter simulator (Member 2): generates readings, optionally with bad data mixed in."""
import random
from datetime import datetime, timedelta

from contracts.events import MeterReading


def generate_readings(meter_ids: list[str], count: int, bad_data: bool = False,
                      seed: int = 42) -> list[MeterReading]:
    rng = random.Random(seed)
    start = datetime(2026, 10, 7, 9, 0, 0)
    readings = []
    for i in range(count):
        ts = (start + timedelta(seconds=5 * i)).isoformat()
        for meter_id in meter_ids:
            readings.append(MeterReading(meter_id, ts, round(rng.uniform(0.0, 0.5), 3)))
    if bad_data and readings:
        readings.append(readings[0])                                   # duplicate
        readings.append(MeterReading(meter_ids[0], "not-a-time", 0.2))  # bad timestamp
        readings.append(MeterReading(meter_ids[0], start.isoformat(), -1.0))  # negative kWh
    return readings
