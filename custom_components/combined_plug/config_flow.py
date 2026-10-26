"""Generic UI setup; no predefined devices or entity IDs."""

from __future__ import annotations

import hashlib

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import CONF_EXCLUDED, CONF_MEASUREMENTS, CONF_SWITCHES, DEFAULT_EXCLUDED, DOMAIN, MEASUREMENT_BY_KEY
from .discovery import discover_sensors


def _measurement_selector(detected: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=[
            selector.SelectOptionDict(value=key, label=MEASUREMENT_BY_KEY[key].label)
            for key in detected
        ],
        multiple=True,
        mode=selector.SelectSelectorMode.LIST,
    ))


class CombinedPlugConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Select any two or more physical Home Assistant outlet switches."""

    VERSION = 2

    def __init__(self) -> None:
        self._name = ""
        self._switches: list[str] = []
        self._detected: list[str] = []

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            switches = list(dict.fromkeys(user_input[CONF_SWITCHES]))
            registry = er.async_get(self.hass)
            if len(switches) < 2:
                errors["base"] = "at_least_two"
            elif any(
                not (entity := registry.async_get(source))
                or not entity.device_id
                or entity.platform == DOMAIN
                or (state := self.hass.states.get(source)) is not None
                   and bool(state.attributes.get("entity_id"))
                for source in switches
            ):
                errors["base"] = "physical_switches_only"
            else:
                # One configuration per unique collection, regardless of order.
                token = ",".join(sorted(switches))
                digest = hashlib.sha256(token.encode()).hexdigest()
                await self.async_set_unique_id(digest)
                self._abort_if_unique_id_configured()
                detected = list(discover_sensors(self.hass, switches))
                if not detected:
                    errors["base"] = "no_common_measurements"
                else:
                    self._name = user_input[CONF_NAME].strip()
                    self._switches = switches
                    self._detected = detected
                    return await self.async_step_measurements()

        schema = vol.Schema({
            vol.Required(CONF_NAME, default="Combined Plug"): selector.TextSelector(),
            vol.Required(CONF_SWITCHES): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch", multiple=True)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_measurements(self, user_input=None):
        """Let the user untick measurements before anything is created."""
        if user_input is not None:
            selected = set(user_input[CONF_MEASUREMENTS])
            excluded = [key for key in self._detected if key not in selected]
            return self.async_create_entry(
                title=self._name,
                data={CONF_SWITCHES: self._switches},
                options={CONF_EXCLUDED: excluded},
            )

        default = [key for key in self._detected if key not in DEFAULT_EXCLUDED]
        schema = vol.Schema({
            vol.Required(CONF_MEASUREMENTS, default=default): _measurement_selector(self._detected),
        })
        return self.async_show_form(step_id="measurements", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CombinedPlugOptionsFlow()


class CombinedPlugOptionsFlow(config_entries.OptionsFlow):
    """Change which detected measurements the virtual outlet exposes."""

    async def async_step_init(self, user_input=None):
        detected = list(discover_sensors(self.hass, list(self.config_entry.data[CONF_SWITCHES])))
        if user_input is not None:
            selected = set(user_input[CONF_MEASUREMENTS])
            return self.async_create_entry(
                title="",
                data={CONF_EXCLUDED: [key for key in detected if key not in selected]},
            )

        current_excluded = self.config_entry.options.get(CONF_EXCLUDED, list(DEFAULT_EXCLUDED))
        default = [key for key in detected if key not in current_excluded]
        schema = vol.Schema({
            vol.Required(CONF_MEASUREMENTS, default=default): _measurement_selector(detected),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
