"""Custom types for the Tyne and Wear Metro integration."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, _LOGGER

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

from .coordinator import MetroDataUpdateCoordinator

if TYPE_CHECKING:
    from .metro import MetroNetwork

type MetroConfigEntry = ConfigEntry[MetroData]


@dataclass
class MetroData:
    """Data for the Tyne and Wear Metro integration."""
    api: MetroNetwork
    coordinator: MetroDataUpdateCoordinator
