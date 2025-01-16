"""Config flow for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import selector
import voluptuous as vol

from .metro import MetroNetwork


class MetroConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    def __init__(self):
        self._data = {
            'platforms': [],
        }
        self._api = MetroNetwork()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        await self._api.hydrate()
        _LOGGER.warning(f'async_step_user: {self._data}')

        schema = {
            vol.Required('new_platform_entry', default='WTL|1'): selector({
                "select": {
                    "options": await self._api.get_platforms_select(),
                },
            }),
        }
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema(schema), errors=errors)
        station_code, platform_code = user_input['new_platform_entry'].split('|')
        self._data['platforms'] = [{
            'name': f'metro_{station_code}_platform_{platform_code}',
            'station_code': station_code,
            'platform_code': platform_code,
            'destination_code': None,
        }]
        _LOGGER.warning(f'async_step_user end: {self._data}')
        return self.async_create_entry(title=f"Tyne and Wear Metro", data=self._data)

    # async def async_step_station(self, user_input: dict[str, Any]) -> ConfigFlowResult:
    #     errors: dict[str, str] = {}
    #     _LOGGER.warning(f'async_step_station: {self._data}')
    #     metro = MetroAPI()
    #     stations = await metro.async_get_stations()
    #     if 'code' not in user_input:
    #         return self.async_show_form(step_id="station", data_schema=vol.Schema({
    #             vol.Required('code', default=user_input.get('code', 'WTL')): selector({
    #                 "select": {
    #                     "options": [{"label": name, "value": code} for code, name in stations.items()],
    #                 },
    #             }),
    #         }), errors=errors)
    #     self._data['station'] = stations[user_input['code']]
    #     self._data.update(user_input)
    #     _LOGGER.warning(f'async_step_station end: {self._data}')
    #     return await self.async_step_platform(user_input)

    # async def async_step_platform(self, user_input: dict[str, Any]) -> ConfigFlowResult:
    #     errors: dict[str, str] = {}
    #     _LOGGER.warning(f'async_step_platform: {self._data}')
    #     metro = MetroAPI()
    #     platforms = await metro.async_get_platforms()
    #     if 'platform' not in user_input:
    #         return self.async_show_form(step_id="platform", data_schema=vol.Schema({
    #             vol.Required('platform', default=user_input.get('platform', '1')): selector({
    #                 "select": {
    #                     "options": [{"label": f"Platform {platform['platformNumber']}: {platform['helperText']}", "value": str(platform['platformNumber'])} for platform in platforms[user_input.get('code', 'WTL')]],
    #                 },
    #             }),
    #         }), errors=errors)
    #     for platform in platforms[self._data['code']]:
    #         if str(platform['platformNumber']) == user_input['platform']:
    #             self._data['platform_text'] = platform['helperText']
    #     self._data.update(user_input)
    #     _LOGGER.warning(f'async_step_platform end: {self._data}')
    #     await self.async_set_unique_id(f"metro_platform_{self._data['code']}_{self._data['platform']}")
    #     self._abort_if_unique_id_configured()
    #     return self.async_create_entry(title=f"{self._data['station']} platform {self._data['platform']}", data=self._data)