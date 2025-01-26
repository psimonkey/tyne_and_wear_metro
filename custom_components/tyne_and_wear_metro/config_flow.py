"""Config flow for the Tyne and Wear Metro integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import _LOGGER, DOMAIN
from .metro import MetroNetwork

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


class MetroConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config Flow for Tyne and Wear Metro integration."""

    VERSION = 1

    def __init__(self):
        self._data = {}
        self._api = MetroNetwork()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        await self._api.hydrate()
        if user_input is None:
            user_input = {}
        return self.async_create_entry(title=f"Tyne and Wear Metro", data=self._data)
