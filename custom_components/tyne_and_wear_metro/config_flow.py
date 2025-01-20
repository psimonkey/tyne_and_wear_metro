"""Config flow for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import selector
import voluptuous as vol

from .metro import MetroNetwork

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

class MetroConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    def __init__(self):
        self._data = {}
        self._api = MetroNetwork()

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry: ConfigEntry) -> MetroOptionsFlow:
    #     return MetroOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        await self._api.hydrate()
        if user_input is None:
            user_input = {}
        schema = {
            vol.Required('start', default=user_input.get('start', 'MSN')): selector({
                "select": {
                    "options": await self._api.get_station_select(),
                },
            }),
            vol.Required('end', default=user_input.get('end', 'MTS')): selector({
                "select": {
                    "options": await self._api.get_station_select(user_input.get('start', None)),
                },
            }),
        }
        if user_input.get('start', 'MSN') == user_input.get('end', 'MTS'):
            errors['end'] = 'Start and destination stations must be different.'
        if user_input is None or user_input == {} or errors:
            return self.async_show_form(step_id="user", data_schema=vol.Schema(schema), errors=errors)
        self._data = {
            'start': user_input['start'],
            'platform': self._api.which_platform(user_input['start'], user_input['end']).code,
            'end': user_input['end'],
        }
        start_name, end_name = self._api.get_station_by_code(user_input['start']).name, self._api.get_station_by_code(user_input['end']).name,
        return self.async_create_entry(title=f"Metro from {start_name} to {end_name}", data=self._data)

    # async def async_step_destination(self, user_input: dict[str, Any]) -> ConfigFlowResult:
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


class MetroOptionsFlow(OptionsFlow):

    VERSION = 1

    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        _LOGGER.warning(f'async_step_init: {self.config_entry}')
        schema = {
            vol.Required('new_platform_entry', default='WTL|1'): selector({
                "select": {
                    "options": await self.config_entry.runtime_data.api.get_platforms_select(),
                },
            }),
        }
        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=vol.Schema(schema), errors=errors)
        station_code, platform_code = user_input['new_platform_entry'].split('|')
        self.config_entry.data['platforms'].append({
            'name': f'metro_{station_code}_platform_{platform_code}',
            'station_code': station_code,
            'platform_code': platform_code,
            'destination_code': None,
        })
        self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
        _LOGGER.warning(f'async_step_init: {self.config_entry}')
        return self.async_create_entry(title="", data={})