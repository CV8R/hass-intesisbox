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
        if controller.is_connected and len(controller.operation_list) > 0:
            # Core initialization is done (have connection and operation modes)
            # Wait a bit longer for optional features (fan speeds, vanes)
            if i >= 60:  # After 6 seconds, proceed even if optional features missing
                # Build log prefix matching the format used elsewhere
                if controller.device_mac_address:
                    entity_id = f"climate.{controller.device_mac_address.lower()}"
                    log_prefix = f"[{name}({entity_id})]"
                else:
                    log_prefix = f"[{host}]"

                _LOGGER.info(
                    "%s Intesis Gateway initialized (fans: %d, vanes: v=%d h=%d)",
                    log_prefix,
                    len(controller.fan_speed_list),
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
            # Wait for connection to ACTUALLY close (not just initiated)
            disconnect_ok = await controller.wait_for_disconnect(timeout=5.0)
            if disconnect_ok:
                # Connection closed successfully, now enforce protocol minimum delay
                _LOGGER.debug("Connection closed, waiting protocol minimum delay")
                await asyncio.sleep(1.0)
            else:
                # Timeout waiting for disconnect, use longer delay to be safe
                _LOGGER.warning("Disconnect timeout, using extended delay")
                await asyncio.sleep(3.0)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
