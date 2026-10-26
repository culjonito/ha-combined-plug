"""Load dependency-free modules without importing HA (not installed in CI here)."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'custom_components' / 'combined_plug'


def load_file(name):
    spec = importlib.util.spec_from_file_location(f'combined_plug.{name}', ROOT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def code():
    package = types.ModuleType('combined_plug')
    package.__path__ = [str(ROOT)]
    sys.modules['combined_plug'] = package
    const = load_file('const')
    calc = load_file('calculation')
    return const, calc


@pytest.fixture
def discovered(code, monkeypatch):
    core = types.ModuleType('homeassistant.core')
    core.HomeAssistant = object
    helpers = types.ModuleType('homeassistant.helpers')
    er = types.ModuleType('homeassistant.helpers.entity_registry')
    er.EntityRegistry = object
    er.async_get = lambda hass: hass.registry
    er.async_entries_for_device = lambda registry, id: [e for e in registry.by_id.values() if e.device_id == id]
    helpers.entity_registry = er
    monkeypatch.setitem(sys.modules, 'homeassistant', types.ModuleType('homeassistant'))
    monkeypatch.setitem(sys.modules, 'homeassistant.core', core)
    monkeypatch.setitem(sys.modules, 'homeassistant.helpers', helpers)
    monkeypatch.setitem(sys.modules, 'homeassistant.helpers.entity_registry', er)
    return load_file('discovery')
