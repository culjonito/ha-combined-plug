"""Generic UI setup; no predefined devices or entity IDs."""

from __future__ import annotations

import hashlib

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_registry as er, selector

from .const import CONF_SWITCHES, DOMAIN
from .discovery import discover_sensors


class CombinedPlugConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Select any two or more physical Home Assistant outlet switches."""

    VERSION = 2

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
                if not discover_sensors(self.hass, switches):
                    errors["base"] = "no_common_measurements"
                else:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME].strip(),
                        data={CONF_SWITCHES: switches},
                    )

        schema = vol.Schema({
            vol.Required(CONF_NAME, default="Combined Plug"): selector.TextSelector(),
            vol.Required(CONF_SWITCHES): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch", multiple=True)
            ),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
