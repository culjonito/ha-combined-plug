from dataclasses import dataclass, field
from types import SimpleNamespace


@dataclass
class FakeRegistryEntry:
    entity_id: str
    device_id: str | None
    device_class: str | None = None
    original_device_class: str | None = None
    name: str | None = None
    original_name: str | None = None
    disabled_by: str | None = None

    @property
    def domain(self):
        return self.entity_id.split('.')[0]


class Registry:
    def __init__(self, entries):
        self.by_id = {e.entity_id: e for e in entries}
    def async_get(self, entity_id):
        return self.by_id.get(entity_id)


class States:
    def __init__(self, values):
        self.values=values
    def get(self, entity_id):
        return self.values.get(entity_id)


def fake_hass(entries):
    states = {
        e.entity_id: SimpleNamespace(attributes={'device_class':e.device_class, 'friendly_name': e.original_name})
        for e in entries if e.domain == 'sensor'
    }
    return SimpleNamespace(registry=Registry(entries), states=States(states))


def test_zha_german_names(discovered):
    entries=[]
    for i in (1,2):
        device = f'physical-{i}'
        prefix=f'test_socket_{i}'
        entries.append(FakeRegistryEntry(f'switch.{prefix}', device))
        for key,cls in [
            ('leistung','power'), ('energie','energy'), ('eingespeiste_energie','energy'),
            ('spannung_effektivwert','voltage'), ('stromstarke_effektivwert','current'),
            ('frequenz','frequency'), ('leistungsfaktor','power_factor'),
        ]:
            entries.append(FakeRegistryEntry(f'sensor.{prefix}_{key}',device,cls))
    result=discovered.discover_sensors(fake_hass(entries), [f'switch.test_socket_{i}' for i in (1,2)])
    assert set(result) == {'power','energy','energy_export','voltage','current','frequency','power_factor'}
    assert result['energy_export'] == [f'sensor.test_socket_{i}_eingespeiste_energie' for i in (1,2)]
    assert result['energy'] == [f'sensor.test_socket_{i}_energie' for i in (1,2)]


def test_english_devices_by_device_registry_not_slug(discovered):
    entries=[
        FakeRegistryEntry('switch.zb_44', 'device1'),
        FakeRegistryEntry('switch.unrelated_abc', 'device2'),
        FakeRegistryEntry('sensor.power_meter_11', 'device1', 'power', original_name='Active power'),
        FakeRegistryEntry('sensor.power_meter_77', 'device2', 'power', original_name='Active power'),
        FakeRegistryEntry('sensor.counter_11', 'device1', 'energy', original_name='Total energy'),
        FakeRegistryEntry('sensor.counter_77', 'device2', 'energy', original_name='Total energy'),
    ]
    result=discovered.discover_sensors(fake_hass(entries), ['switch.zb_44','switch.unrelated_abc'])
    assert result['power']==['sensor.power_meter_11','sensor.power_meter_77']
    assert result['energy']==['sensor.counter_11','sensor.counter_77']
    assert 'voltage' not in result


def test_ambiguous_measurements_skipped(discovered):
    entries=[FakeRegistryEntry('switch.p1','a'),FakeRegistryEntry('switch.p2','b')]
    for device in ('a','b'):
        entries.extend([
            FakeRegistryEntry(f'sensor.{device}_p1',device,'power'),
            FakeRegistryEntry(f'sensor.{device}_p2',device,'power'),
        ])
    result=discovered.discover_sensors(fake_hass(entries), ['switch.p1','switch.p2'])
    assert 'power' not in result


def test_disabled_measurement_and_duplicate_device(discovered):
    entries=[FakeRegistryEntry('switch.p1','a'),FakeRegistryEntry('switch.p2','b'),
        FakeRegistryEntry('sensor.a_voltage','a','voltage'),
        FakeRegistryEntry('sensor.b_voltage','b','voltage',disabled_by='user')]
    assert not discovered.discover_sensors(fake_hass(entries),['switch.p1','switch.p2'])
    entries[1].device_id='a'
    entries[3].device_id='a'
    assert not discovered.discover_sensors(fake_hass(entries),['switch.p1','switch.p2'])
