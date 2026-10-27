"""Data definitions for Combined Plug; never contains user-specific entities."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "combined_plug"
CONF_SWITCHES = "switches"
# Entity IDs this integration hid on the source outlets; restored on removal.
CONF_HIDDEN = "hidden_entities"


@dataclass(frozen=True, slots=True)
class Measurement:
    key: str
    device_class: str
    unit: str
    aggregation: str
    decimals: int
    keywords: tuple[str, ...]


MEASUREMENTS = (
    Measurement("power", "power", "W", "sum", 2, (
        "power", "active_power", "leistung", "watt", "power_consumption", "wirkleistung",
    )),
    Measurement("energy", "energy", "kWh", "sum", 4, (
        "energy", "energie", "consumption", "verbrauch", "kwh", "electricity", "import", "delivered",
    )),
    Measurement("energy_export", "energy", "kWh", "sum", 4, (
        "export", "exported", "returned", "return", "einspeisung", "eingespeist", "eingespeiste", "feed_in", "production", "injected", "ruecklieferung",
    )),
    Measurement("voltage", "voltage", "V", "average", 2, (
        "voltage", "spannung", "rms_voltage", "volt",
    )),
    Measurement("current", "current", "A", "sum", 3, (
        "current", "stromstaerke", "stromstarke", "strom", "amperage", "rms_current",
    )),
    Measurement("frequency", "frequency", "Hz", "average", 2, (
        "frequency", "frequenz", "hz",
    )),
    Measurement("power_factor", "power_factor", "%", "weighted_average", 1, (
        "power_factor", "leistungsfaktor", "cos_phi", "cosphi",
    )),
)
MEASUREMENT_BY_KEY = {item.key: item for item in MEASUREMENTS}
EXPORT_WORDS = MEASUREMENT_BY_KEY["energy_export"].keywords

# Canonical output units; variants not listed are rejected, not silently mixed.
CONVERSIONS = {
    "power": {"W": 1, "kW": 1_000, "mW": .001},
    "energy": {"kWh": 1, "Wh": .001, "MWh": 1_000},
    "energy_export": {"kWh": 1, "Wh": .001, "MWh": 1_000},
    "voltage": {"V": 1, "mV": .001, "kV": 1_000},
    "current": {"A": 1, "mA": .001},
    "frequency": {"Hz": 1, "kHz": 1_000},
    "power_factor": {"%": 1, "": 100},
}
