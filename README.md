# Combined Plug

One virtual Home Assistant outlet from two or more physical outlets. **No YAML, automation, MQTT or Helper entities needed.**

**Early public-release candidate (0.2.0): not yet verified against a live Home Assistant instance.**

## Features

- Set up from **Settings → Devices & services → Add integration → Combined Plug**.
- Choose a name and any two or more physical switch entities.
- The integration creates **one virtual device** with **one switch** controlling all source outlets.
- Automatically detects compatible measurement sensors from each source outlet's **device registry**. This works with ZHA and other integrations exposing regular Home Assistant sensor entities.
- Combines readings into the virtual device (only if all selected outlets have the matching measurement):

| Sensor | Method |
| --- | --- |
| Power (W) | Sum |
| Energy (kWh) | Sum |
| Exported energy (kWh) | Sum |
| Current (A) | Sum (physically meaningful as total circuit current only on the same phase) |
| Voltage (V) | Arithmetic mean |
| Frequency (Hz) | Arithmetic mean |
| Power factor (%) | Apparent-power-weighted average when voltage and current are available; otherwise arithmetic mean |

- Values refresh in response to source changes, not on a polling timer.
- Source outlets remain fully independent physical devices; the integration does **not** merge the original Zigbee/ZHA devices or alter their registry entries.
- One Home Assistant config entry can represent one group; add Combined Plug again for additional groups.

## Installation

### Before GitHub publication: local manual install

1. Copy `custom_components/combined_plug/` into the Home Assistant configuration directory under `custom_components/combined_plug/`.
2. Restart Home Assistant.
3. Add the integration through **Settings → Devices & services → Add integration → Combined Plug**.
4. Select **two or more physical switches** and a name.

### After you publish the repository

1. In HACS, choose **Custom repositories** and enter your **actual public GitHub repository URL** (type: **Integration**).
2. Install **Combined Plug** and restart Home Assistant if required.
3. Go to **Settings → Devices & services → Add integration → Combined Plug**, name your group, and select physical switches.

A repository is **not** automatically searchable in the default HACS catalogue just because its files conform to HACS. Users can add it as a custom repository once it is public; the listing in the default catalogue requires a separate submission/review.

## Requirements and limitations

- **No device names or entity IDs are hardcoded.** Detection relies on each selected switch having its own Home Assistant **device registry** entry and on each measurement being assigned to the *same physical device* as that switch.
- The integration only offers sensors supported by **all** selected physical outlets. A measurement with an ambiguous match on a device is omitted to avoid potentially incorrect values.
- It requires at least one shared measurement. This integration is designed for metered outlets, not ordinary switch groups.
- If you previously merged physical devices using **Device Tools**, undo the merge first: otherwise the physical sensors may no longer have unique device associations.
- Sensors disabled in the entity registry will not be discovered. Enable the desired measurements first.
- After changing source devices or enabling new measurements, remove and re-add the Combined Plug entry to re-run discovery. Automatically adding new measurement types later is not yet supported.
- **Power factor:** percentages and fractions with explicit `%`/unitless representations are converted; device-specific values should be checked.
- **Energy statistics warning:** if one underlying cumulative energy counter resets, the summed counter may decrease. It is deliberately exposed as `total` rather than `total_increasing` to avoid a false zero-reset interpretation, but even this does **not** make it a perfect energy dashboard source for independently resetting counters. For an accurate Home Assistant Energy Dashboard, add the original outlets' energy sensors separately, without also adding their Combined Plug energy sum (or you would double-count).
- Source availability: computed sensors are `unavailable` if any required measurement is unavailable or nonnumeric.
- Toggle behavior: the virtual outlet reports `on` when **any** member is on. Switching it on/off always targets **every** member.

## Publishing as your own HACS repository

Create a **public** GitHub repository, e.g. `ha-combined-plug`, and push the **contents of this archive** to its root. Before publishing:

1. Replace `YOUR_GITHUB_USERNAME` in `custom_components/combined_plug/manifest.json` with the real GitHub owner (also update the repository name in the URLs if different).
2. Set `codeowners` in `manifest.json` to your GitHub username, for example `["@yourname"]`.
3. Configure the GitHub project description, topics (e.g. `home-assistant`, `hacs`, `custom-integration`, `zigbee`), issue tracker, and a release like `v0.2.0`.
4. Run [HACS validation](https://github.com/hacs/action) and [Hassfest](https://github.com/home-assistant/actions) from the supplied GitHub workflows. Address their reports before applying to the official catalogue.
5. For inclusion in HACS' standard catalogue, submit a request through the official [HACS repository submission process](https://www.hacs.dev/docs/publish/include/). Until approved, users install it as a custom repository.

The included `brand/icon.png` is a generic app icon; replace it with your own if desired.

## Developer tests

Lightweight tests for the pure aggregations and sensor mapping are in `tests/` and can run with Python + pytest without Home Assistant. **They do not replace real-instance testing.**

## License

MIT, see [LICENSE](LICENSE).
