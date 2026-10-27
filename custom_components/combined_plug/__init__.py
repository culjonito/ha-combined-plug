"""Combined Plug: multiple real outlets, one virtual device."""

from __future__ import annotations

import hashlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .calculation import replace_entity_id
from .const import CONF_HIDDEN, CONF_SWITCHES
from .discovery import discover_sensors

PLATFORMS = (Platform.SWITCH, Platform.SENSOR)


class CombinedPlugRuntime:
    """One event listener updates all virtual entities only when sources change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.switches: list[str] = list(entry.data[CONF_SWITCHES])
        self.sensors: dict[str, list[str]] = discover_sensors(hass, self.switches)
        self._entities: set = set()

    def source_entities(self) -> set[str]:
        """Every outlet switch and every measurement sensor that feeds the combined outlet."""
        sources = set(self.switches)
        for sensor_ids in self.sensors.values():
            sources.update(sensor_ids)
        return sources

    def start(self) -> None:
        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, self.source_entities(), self._source_changed)
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
def _set_hidden(hass: HomeAssistant, entity_id: str, hidden: bool) -> None:
    """Hide or unhide an entity, touching only entries hidden by the user setting."""
    registry = er.async_get(hass)
    ent = registry.async_get(entity_id)
    if ent is None:
        return
    if hidden and ent.hidden_by is None:
        registry.async_update_entity(entity_id, hidden_by=er.RegistryEntryHider.USER)
    elif not hidden and ent.hidden_by == er.RegistryEntryHider.USER:
        registry.async_update_entity(entity_id, hidden_by=None)


@callback
def _sync_visibility(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hide the source outlets' switches and used sensors; they live on the combined device now."""
    desired = entry.runtime_data.source_entities()
    previous = set(entry.data.get(CONF_HIDDEN, []))
    for entity_id in previous - desired:
        _set_hidden(hass, entity_id, False)
    for entity_id in desired:
        _set_hidden(hass, entity_id, True)
    if previous != desired:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_HIDDEN: sorted(desired)}
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = CombinedPlugRuntime(hass, entry)
    entry.runtime_data = runtime
    runtime.start()
    _sync_visibility(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Deleting the combined outlet gives the original outlets back."""
    for entity_id in entry.data.get(CONF_HIDDEN, []):
        _set_hidden(hass, entity_id, False)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate previously configured fixed-two-outlet entries without losing them."""
    if entry.version == 1:
        switches = list(entry.data[CONF_SWITCHES])
        identity = hashlib.sha256(",".join(sorted(switches)).encode()).hexdigest()
        hass.config_entries.async_update_entry(
            entry, data={CONF_SWITCHES: switches}, unique_id=identity, version=2
        )
    return entry.version == 2
