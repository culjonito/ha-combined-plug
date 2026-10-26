"""Summed and averaged measurements for a combined outlet."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .calculation import combine, normalize
from .const import MEASUREMENT_BY_KEY
from .entity import CombinedPlugEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime = entry.runtime_data
    async_add_entities(CombinedPlugSensor(runtime, key) for key in runtime.sensors)


class CombinedPlugSensor(CombinedPlugEntity, SensorEntity):
    """Computed from all sensors of the selected outlets; never polls."""

    def __init__(self, runtime, key: str) -> None:
        super().__init__(runtime, key)
        self.key = key
        measurement = MEASUREMENT_BY_KEY[key]
        self._attr_name = measurement.label
        self._attr_device_class = SensorDeviceClass(measurement.device_class)
        self._attr_native_unit_of_measurement = measurement.unit
        # Summed source counters can decrease when only one plug resets;
        # TOTAL (rather than TOTAL_INCREASING) avoids treating the drop as
        # a new meter cycle and inflating consumption. See README warning.
        self._attr_state_class = (
            SensorStateClass.TOTAL
            if key in ("energy", "energy_export")
            else SensorStateClass.MEASUREMENT
        )
        self._attr_suggested_display_precision = measurement.decimals

    def _reading(self, key: str, index: int) -> float | None:
        if key not in self.runtime.sensors:
            return None
        source = self.runtime.sensors[key][index]
        state = self.hass.states.get(source)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        return normalize(key, state.state, state.attributes.get("unit_of_measurement"))

    def _calculate(self) -> float | None:
        values = [self._reading(self.key, n) for n in range(len(self.runtime.switches))]
        if any(value is None for value in values):
            return None
        weights = None
        if self.key == "power_factor":
            voltages = [self._reading("voltage", n) for n in range(len(values))]
            currents = [self._reading("current", n) for n in range(len(values))]
            if all(value is not None for value in (*voltages, *currents)):
                weights = [max(0, v * a) for v, a in zip(voltages, currents, strict=True)]
        result = combine(self.key, values, weights)
        return round(result, MEASUREMENT_BY_KEY[self.key].decimals) if result is not None else None

    @property
    def available(self) -> bool:
        return self._calculate() is not None

    @property
    def native_value(self) -> float | None:
        return self._calculate()
