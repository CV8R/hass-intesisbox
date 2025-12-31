"""The Intesis integration for Intesis Air Conditioning Gateways (WMP Protocol)."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.const import CONF_HOST, Platform  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore

from .const import DOMAIN
from .intesisbox import IntesisBox

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intesis Gateway from a config entry."""
    host = entry.data[CONF_HOST]
    name = entry.title

    _LOGGER.info("Setting up Intesis Gateway integration for %s", host)

    # Create controller
    controller = IntesisBox(host, loop=hass.loop, name=name)

    # Store controller first
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = controller

    # Connect to device (this is synchronous but schedules async work)
    _LOGGER.debug("Calling controller.connect()")
    controller.connect()

    # Wait for the connection to be established and initialized
    _LOGGER.debug("Waiting for connection and initialization...")
    for i in range(150):  # Wait up to 15 seconds for all limits including vanes
        if (
            controller.is_connected
            and len(controller.fan_speed_list) > 0
            and len(controller.operation_list) > 0
        ):
            # Core initialization is done, wait a bit longer for vanes
            # Vanes are queried after MODE, so they arrive later
            if i >= 60:  # After 6 seconds, proceed (vanes should be loaded by then)
                # Build log prefix matching the format used elsewhere
                if controller.device_mac_address:
                    entity_id = f"climate.{controller.device_mac_address.lower()}"
                    log_prefix = f"[{name}({entity_id})]"
                else:
                    log_prefix = f"[{host}]"

                _LOGGER.info(
                    "%s Intesis Gateway initialized (vanes: v=%d h=%d)",
                    log_prefix,
                    len(controller.vane_vertical_list),
                    len(controller.vane_horizontal_list),
                )
                break
        await asyncio.sleep(0.1)
    else:
        _LOGGER.warning(
            "Initialization timeout after 15 seconds (device may still be initializing)"
        )

    # Forward entry setup to climate platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Intesis Gateway integration for %s", entry.data[CONF_HOST])

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop and remove controller
        controller = hass.data[DOMAIN].pop(entry.entry_id, None)
        if controller:
            _LOGGER.debug("Stopping controller")
            controller.stop()
            # Give it a moment to cleanup
            await asyncio.sleep(0.1)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
