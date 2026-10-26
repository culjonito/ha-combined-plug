"""Shared virtual device identity for the switch and measured sensors."""

from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class CombinedPlugEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, runtime, key: str) -> None:
        self.runtime = runtime
        self._attr_unique_id = f"{runtime.entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, runtime.entry.entry_id)},
            "name": runtime.entry.title,
            "manufacturer": "Combined Plug",
            "model": "Virtual combined outlet",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.runtime.add(self)

    async def async_will_remove_from_hass(self) -> None:
        self.runtime.remove(self)
        await super().async_will_remove_from_hass()
