# Intesis Gateway for Home Assistant

Control Intesis Air Conditioning Gateways locally via the WMP Protocol.

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/jnimmo/hass-intesisbox`
6. Select "Integration" as the category
7. Click "Add"
8. Click "Install" on the IntesisBox card that appears
9. Restart Home Assistant
10. Go to Settings → Devices & Services
11. Click "Add Integration"
12. Search for "Intesis Gateway" and select it
13. Enter your Intesis Gateway IP address as the host

### Option 2: Manual Installation

1. Download the `intesisbox` directory from this repository
2. Copy it into your `custom_components` directory (create it if it doesn't exist)
3. Restart Home Assistant
4. Go to Settings → Devices & Services
5. Click "Add Integration"
6. Search for "Intesis Gateway" and select it
7. Enter your Intesis Gateway IP address and name it

## Configuration

**Settings → Devices & Services → Add Integration → "Intesis Gateway"**

Fan and Swing modes can be customized after setup via Gear Icon in the Intesis Gateway Integration.

## Troubleshooting

**Device Unavailable:**
- Verify IP address and network connectivity
- Check port 3310 is not blocked

### Debug Logging

Add the logger configuration to `configuration.yaml` and restart Home Assistant.
```yaml
  logs:
    custom_components.intesisbox: debug
```

## IntesisBox Emulator

Emulates IntesisBox WMP protocol device on TCP port 3310.

### Usage

```bash
# Run with defaults
python IntesisBoxEmulator.py

# Get help
python IntesisBoxEmulator.py --help

# Example with custom V/H vane and fan positions
python IntesisBoxEmulator.py --VUD A7S --VLR A5S --FAN A4
```

### Compact Notation Format

Pattern: `[A][X][S]`
* A = includes AUTO
* X = number of positions (1-9)
* S = includes SWING (vanes only, not for fan)
* N = disabled (LIMITS queries are ignored, no response sent)

### Allow dynamic min max temp limits per mode

--dynamic-setptemp

Enables dynamic temperature limits based on current MODE

Default: Disabled (static limits [180,300])

### Support setting and tracking time

- **CFG:DATETIME** - Get current internal date and time
  - Format: `CFG:DATETIME,DD/MM/YYYY HH:MM:SS`
  - Example response: `CFG:DATETIME,31/12/2001 19:18:31`
- **CFG:DATETIME,DD/MM/YYYY HH:MM:SS** - Set internal date and time
  - Example: `CFG:DATETIME,31/12/2025 23:59:50`
  - Response: `ACK` (or `ERR` if format invalid)

## Credits

Original: [@jnimmo](https://github.com/jnimmo)
