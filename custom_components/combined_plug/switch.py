"""One outlet switch for all selected source outlets."""

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import CombinedPlugEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([CombinedPlugSwitch(entry.runtime_data)])


class CombinedPlugSwitch(CombinedPlugEntity, SwitchEntity):
    _attr_name = None  # The main (unnamed) entity of the device
    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, runtime) -> None:
        super().__init__(runtime, "switch")

    @property
    def available(self) -> bool:
        return all(
            (state := self.hass.states.get(entity_id)) is not None
            and state.state in ("on", "off")
            for entity_id in self.runtime.switches
        )

    @property
    def is_on(self) -> bool:
        # A partially switched-on group is considered on. Switching off
        # always turns off every member; switching on turns on every member.
        return any(self.hass.states.is_state(entity_id, "on") for entity_id in self.runtime.switches)

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self.runtime.switches}, blocking=True
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self.runtime.switches}, blocking=True
        )
