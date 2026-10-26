"""Combined Plug: multiple real outlets, one virtual device."""

from __future__ import annotations

import hashlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .calculation import active_measurements, replace_entity_id
from .const import CONF_EXCLUDED, CONF_HIDE_SOURCES, CONF_SWITCHES, DEFAULT_EXCLUDED
from .discovery import discover_sensors

PLATFORMS = (Platform.SWITCH, Platform.SENSOR)


class CombinedPlugRuntime:
    """One event listener updates all virtual entities only when sources change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.switches: list[str] = list(entry.data[CONF_SWITCHES])
        excluded = entry.options.get(CONF_EXCLUDED, list(DEFAULT_EXCLUDED))
        self.sensors: dict[str, list[str]] = active_measurements(
            discover_sensors(hass, self.switches), excluded
        )
        self._entities: set = set()

    def start(self) -> None:
        sources = set(self.switches)
        for sensor_ids in self.sensors.values():
            sources.update(sensor_ids)
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, sources, self._source_changed)
        )
        self.entry.async_on_unload(
            self.hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, self._registry_updated)
        )

    @callback
    def _source_changed(self, event: Event) -> None:
        for entity in tuple(self._entities):
            entity.async_write_ha_state()

    @callback
    def _registry_updated(self, event: Event) -> None:
        """Follow renamed source entities, otherwise the stored IDs silently go stale."""
        if event.data.get("action") != "update" or "old_entity_id" not in event.data:
            return
        old, new = event.data["old_entity_id"], event.data["entity_id"]
        if old not in self.switches:
            return
        self.hass.config_entries.async_update_entry(
            self.entry,
            data={**self.entry.data, CONF_SWITCHES: replace_entity_id(self.switches, old, new)},
        )
        self.hass.config_entries.async_schedule_reload(self.entry.entry_id)

    @callback
    def add(self, entity) -> None:
        self._entities.add(entity)

    @callback
    def remove(self, entity) -> None:
        self._entities.discard(entity)


@callback
def _apply_source_visibility(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hide or unhide the physical outlets' entities, as chosen in the options.

    Only entities hidden by this integration (hidden_by=user) are touched when unhiding,
    so entities you hid yourself are not reset by accident.
    """
    registry = er.async_get(hass)
    runtime = entry.runtime_data
    sources = set(runtime.switches)
    for sensor_ids in runtime.sensors.values():
        sources.update(sensor_ids)
    hide = entry.options.get(CONF_HIDE_SOURCES, False)
    for entity_id in sources:
        ent = registry.async_get(entity_id)
        if ent is None:
            continue
        if hide and ent.hidden_by is None:
            registry.async_update_entity(entity_id, hidden_by=er.RegistryEntryHider.USER)
        elif not hide and ent.hidden_by == er.RegistryEntryHider.USER:
            registry.async_update_entity(entity_id, hidden_by=None)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Options changed: rebuild with the new measurement selection."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = CombinedPlugRuntime(hass, entry)
    entry.runtime_data = runtime
    runtime.start()
    _apply_source_visibility(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Deleting the combined outlet gives the original outlets back."""
    if not entry.options.get(CONF_HIDE_SOURCES, False):
        return
    registry = er.async_get(hass)
    for entity_id in entry.data.get(CONF_SWITCHES, []):
        source = registry.async_get(entity_id)
        if source is None or source.device_id is None:
            continue
        for ent in er.async_entries_for_device(registry, source.device_id):
            if ent.hidden_by == er.RegistryEntryHider.USER:
                registry.async_update_entity(ent.entity_id, hidden_by=None)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate previously configured fixed-two-outlet entries without losing them."""
    if entry.version == 1:
        switches = list(entry.data[CONF_SWITCHES])
        identity = hashlib.sha256(",".join(sorted(switches)).encode()).hexdigest()
        hass.config_entries.async_update_entry(
            entry, data={CONF_SWITCHES: switches}, unique_id=identity, version=2
        )
    return entry.version == 2
