"""Switches of the combined outlet: one main switch plus one per source outlet."""

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .entity import CombinedPlugEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime = entry.runtime_data
    entities = [CombinedPlugSwitch(runtime)]
    entities += [CombinedPlugOutletSwitch(runtime, hass, source) for source in runtime.switches]
    async_add_entities(entities)


class CombinedPlugSwitch(CombinedPlugEntity, SwitchEntity):
    """Controls all source outlets together."""

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


class CombinedPlugOutletSwitch(CombinedPlugEntity, SwitchEntity):
    """Controls one source outlet inside the combined device, named like the original."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, runtime, hass: HomeAssistant, source: str) -> None:
        super().__init__(runtime, f"outlet_{source}")
        self._source = source
        self._attr_name = _display_name(hass, source)

    @property
    def available(self) -> bool:
        state = self.hass.states.get(self._source)
        return state is not None and state.state in ("on", "off")

    @property
    def is_on(self) -> bool:
        return self.hass.states.is_state(self._source, "on")

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self._source}, blocking=True
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self._source}, blocking=True
        )


def _display_name(hass: HomeAssistant, entity_id: str) -> str:
    """The name the original outlet has in Home Assistant, falling back to its ID."""
    state = hass.states.get(entity_id)
    if state is not None and state.attributes.get("friendly_name"):
        return state.attributes["friendly_name"]
    entry = er.async_get(hass).async_get(entity_id)
    return (entry.name or entry.original_name) if entry else entity_id
