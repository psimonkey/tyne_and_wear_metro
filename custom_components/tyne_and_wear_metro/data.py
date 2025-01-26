"""Custom types for the Tyne and Wear Metro integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

from .coordinator import MetroDataUpdateCoordinator

if TYPE_CHECKING:
    from .metro import MetroNetwork

type MetroConfigEntry = ConfigEntry[MetroData]


@dataclass
class MetroData:
    """Data for the Tyne and Wear Metro integration."""

    api: MetroNetwork
    coordinator: MetroDataUpdateCoordinator
