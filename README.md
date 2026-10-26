# Combined Plug

One virtual Home Assistant outlet from two or more physical outlets. No YAML, automations, MQTT or helper entities needed.

**Status: 0.4.0. Unit-tested, but not yet verified against a live Home Assistant instance. Please report issues.**

## Features

- Set up from **Settings → Devices & services → Add integration → Combined Plug**.
- Choose a name and two or more physical switch entities, then tick the measurements to include (setup step).
- Creates **one virtual device** with a **main switch** for all source outlets, plus **one switch per source outlet** so each can be switched individually.
- Optional: hide the original outlets' entities, so only the combined outlet is visible.
- Available in English and German; follows Home Assistant's language.
- Detects measurement sensors from each source outlet's **device registry** (works with ZHA, Matter and other integrations that expose regular Home Assistant sensor entities).
- Combines readings only when every selected outlet provides the matching measurement:

| Sensor | Method |
| --- | --- |
| Power (W) | Sum |
| Energy (kWh) | Sum |
| Exported energy (kWh) | Sum (excluded by default, see Options) |
| Current (A) | Sum (only meaningful if all outlets are on the same phase) |
| Voltage (V) | Arithmetic mean |
| Frequency (Hz) | Arithmetic mean |
| Power factor (%) | Apparent-power-weighted average when voltage and current are available; otherwise arithmetic mean |

- Values refresh when source entities change, not on a polling timer.
- Source outlets remain independent physical devices; their registry entries are not altered.
- Renaming a source switch is followed automatically; the integration reloads with the new entity ID.
- One config entry represents one group. Add Combined Plug again for additional groups.

## Measurements

During setup (and later via **Configure**), untick any measurement the virtual outlet should not expose, and choose whether to hide the original outlets. Exported energy is unticked by default. Hiding only affects entities that were hidden by this integration; deleting the combined outlet unhides them again.

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
- Sensors disabled in the entity registry are not discovered. Enable the desired measurements first.
- Source devices or measurements added later are not discovered automatically. Reload the integration (or remove and re-add it) to re-run discovery.
- Do not merge the source devices with Device Tools; merged devices lose their unique sensor associations.
- **Power factor** is unavailable while source outlets report it as `unknown`.
- **Energy statistics:** the summed energy counter is exposed as `total`, not `total_increasing`, so a reset on one source cannot be mistaken for a new meter cycle. Do not add both the combined energy sensor and the individual outlets to the Energy Dashboard, or consumption is counted twice.
- Toggle behaviour: the virtual outlet reports `on` when **any** member is on. Switching it on or off always targets **every** member.
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
