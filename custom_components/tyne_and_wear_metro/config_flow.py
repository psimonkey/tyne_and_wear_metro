"""Config flow for the Tyne and Wear Metro integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class MetroConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config Flow for Tyne and Wear Metro integration."""

    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is None:
            user_input = {}
        return self.async_create_entry(title="Tyne and Wear Metro", data=self._data)
