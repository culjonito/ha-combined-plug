"""Combined Plug: multiple real outlets, one virtual device."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
import hashlib
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_SWITCHES
from .discovery import discover_sensors

PLATFORMS = (Platform.SWITCH, Platform.SENSOR)


class CombinedPlugRuntime:
    """One event listener updates all virtual entities only when sources change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.switches: list[str] = list(entry.data[CONF_SWITCHES])
        # Use stored mapping from the previous version if present; otherwise
        # automatically discover from any HA-compatible physical outlet.
        self.sensors: dict[str, list[str]] = discover_sensors(hass, self.switches)
        self._entities: set = set()

    def start(self) -> None:
        sources = set(self.switches)
        for sensor_ids in self.sensors.values():
            sources.update(sensor_ids)
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, sources, self._source_changed)
        )

    @callback
    def _source_changed(self, event: Event) -> None:
        for entity in tuple(self._entities):
            entity.async_write_ha_state()

    @callback
    def add(self, entity) -> None:
        self._entities.add(entity)

    @callback
    def remove(self, entity) -> None:
        self._entities.discard(entity)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = CombinedPlugRuntime(hass, entry)
    entry.runtime_data = runtime
    runtime.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate previously configured fixed-two-outlet entries without losing them."""
    if entry.version == 1:
        switches = list(entry.data[CONF_SWITCHES])
        identity = hashlib.sha256(",".join(sorted(switches)).encode()).hexdigest()
        hass.config_entries.async_update_entry(
            entry, data={CONF_SWITCHES: switches}, unique_id=identity, version=2
        )
    return entry.version == 2
