"""Match sensors to selected physical outlets through the HA entity registry.

Supports ZHA, Matter and other integrations. Never assumes specific entity IDs or names.
If a device exposes ambiguous sensors, leave that measurement out rather than
silently selecting the wrong one.
"""

from __future__ import annotations

import logging
import re
import unicodedata

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import EXPORT_WORDS, MEASUREMENTS, Measurement

_LOGGER = logging.getLogger(__name__)


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower().replace("ß", "ss"))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _matches(text: str, word: str) -> bool:
    token = _slug(word)
    return bool(re.search(rf"(?:^|_){re.escape(token)}(?:_|$)", text))


def _sensor_class(hass: HomeAssistant, entity) -> str | None:
    state = hass.states.get(entity.entity_id)
    return (
        (state.attributes.get("device_class") if state else None)
        or entity.device_class
        or entity.original_device_class
    )


def _candidate_label(hass: HomeAssistant, entity) -> str:
    state = hass.states.get(entity.entity_id)
    return _slug(" ".join(filter(None, (
        entity.entity_id, entity.name, entity.original_name,
        state.attributes.get("friendly_name") if state else None,
    ))))


def _score(hass: HomeAssistant, entity, measurement: Measurement) -> int:
    """Return 0 for a clearly wrong match, otherwise a score from class and names."""
    cls = _sensor_class(hass, entity)
    if cls and cls != measurement.device_class:
        return 0
    label = _candidate_label(hass, entity)
    matched = [word for word in measurement.keywords if _matches(label, word)]
    if measurement.key == "energy" and any(_matches(label, word) for word in EXPORT_WORDS):
        return 0
    if measurement.key == "energy_export" and not matched:
        return 0
    return (10 if cls == measurement.device_class else 0) + (2 * len(matched))


def _source_sensor(hass: HomeAssistant, registry: er.EntityRegistry, switch_id: str, measurement: Measurement) -> str | None:
    source = registry.async_get(switch_id)
    if source is None or not source.device_id:
        _LOGGER.debug("Cannot discover sensors for %s: no source device", switch_id)
        return None
    candidates = []
    for entity in er.async_entries_for_device(registry, source.device_id):
        if entity.domain != "sensor" or entity.disabled_by is not None:
            continue
        score = _score(hass, entity, measurement)
        if score:
            candidates.append((score, entity.entity_id))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        _LOGGER.debug("Ambiguous %s sensors for %s; ignoring", measurement.key, switch_id)
        return None
    return candidates[0][1]


def discover_matrix(hass: HomeAssistant, switches: list[str]) -> dict[str, list[str | None]]:
    """For every measurement, the matching sensor per outlet (None where missing)."""
    registry = er.async_get(hass)
    return {
        measurement.key: [_source_sensor(hass, registry, entity_id, measurement) for entity_id in switches]
        for measurement in MEASUREMENTS
    }


def discover_sensors(hass: HomeAssistant, switches: list[str]) -> dict[str, list[str]]:
    """Only measurements present on every selected, different outlet."""
    return {
        key: found
        for key, found in discover_matrix(hass, switches).items()
        if all(found) and len(set(found)) == len(switches)
    }
