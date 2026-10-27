# Combined Plug

<img src="custom_components/combined_plug/brand/icon.png" alt="Combined Plug" width="160">

One virtual Home Assistant outlet from two or more physical outlets. No YAML, automations, MQTT or helper entities needed.

**Status: 0.6.0. Unit-tested, but not yet verified against a live Home Assistant instance. Please report issues.**

## Features

- Set up from **Settings → Devices & services → Add integration → Combined Plug**: give it a name and pick two or more outlets. Every measurement they all share is combined; there are no options to choose.
- Creates **one virtual device** with:
  - a **main switch** that switches all source outlets,
  - **one switch per source outlet**, named as the original outlet is named in Home Assistant,
  - **one sensor per combined measurement**.
- The original outlets' switches and the sensors used for combining are **hidden** on their devices, so the combined device is the only place you see them. Hidden entities keep working. Deleting the combined outlet unhides them again.
- Detects measurement sensors from each source outlet's **device registry** (ZHA, Matter and other integrations that expose regular sensor entities).
- Combines readings only when **every** selected outlet provides the measurement. A measurement that only some outlets have is not combined, so no value is ever a partial sum; it stays visible on the original outlet.

| Sensor | Method |
| --- | --- |
| Power (W) | Sum |
| Energy (kWh) | Sum |
| Exported energy (kWh) | Sum |
| Current (A) | Sum (only meaningful if all outlets are on the same phase) |
| Voltage (V) | Arithmetic mean |
| Frequency (Hz) | Arithmetic mean |
| Power factor (%) | Apparent-power-weighted average when voltage and current are available; otherwise arithmetic mean |

- Values refresh when source entities change, not on a polling timer.
- Names and entity labels follow Home Assistant's language (English and German).
- Renaming a source outlet is followed automatically.
- One config entry represents one group. Add Combined Plug again for additional groups.

## Installation

### Manual

1. Copy `custom_components/combined_plug/` into your Home Assistant configuration directory under `custom_components/combined_plug/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Combined Plug**.
4. Select two or more physical switches and a name.

### HACS (custom repository)

1. In HACS, open **Custom repositories**, add `https://github.com/culjonito/ha-combined-plug` with type **Integration**.
2. Install **Combined Plug**, restart Home Assistant, then add the integration as above.

## Requirements and limitations

- **No device names or entity IDs are hardcoded.** Detection relies on each selected switch having its own device registry entry and on each measurement being assigned to the *same physical device* as that switch.
- A measurement is only offered if all selected outlets provide it. Ambiguous matches on a device are omitted rather than guessed.
- Sensors that are disabled in the entity registry are not discovered (disabled entities have no state, so they cannot be combined). Enable the desired measurements first.
- Source devices or measurements added later are not discovered automatically. Reload the integration (or remove and re-add it) to re-run discovery.
- Do not merge the source devices with Device Tools; merged devices lose their unique sensor associations.
- **Power factor** is unavailable while source outlets report it as `unknown`.
- **Energy statistics:** the summed energy counter is exposed as `total`, not `total_increasing`, so a reset on one source cannot be mistaken for a new meter cycle. Use the combined energy sensor in the Energy Dashboard, not the individual outlets, or consumption is counted twice.
- The main switch reports `on` when **any** outlet is on. Switching it always targets **every** outlet.
- Sources that become unavailable make the computed sensors unavailable.

## Development

Pure aggregation, option and rename helpers are tested without Home Assistant:

```
pip install pytest
pytest tests
```

These tests do not replace testing against a real instance.

## License

MIT, see [LICENSE](LICENSE).
