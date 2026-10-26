"""Pure helpers for options and renamed source entities."""


def test_default_exclusion_drops_export_only(code):
    _, calc = code
    discovered = {"power": ["a", "b"], "energy_export": ["c", "d"]}
    assert calc.active_measurements(discovered, ["energy_export"]) == {"power": ["a", "b"]}


def test_empty_exclusion_keeps_everything(code):
    _, calc = code
    discovered = {"power": ["a", "b"], "current": ["c", "d"]}
    assert calc.active_measurements(discovered, []) == discovered


def test_replace_entity_id_keeps_order(code):
    _, calc = code
    assert calc.replace_entity_id(["switch.a", "switch.b"], "switch.b", "switch.c") == ["switch.a", "switch.c"]


def test_replace_entity_id_ignores_unknown(code):
    _, calc = code
    assert calc.replace_entity_id(["switch.a", "switch.b"], "switch.x", "switch.y") == ["switch.a", "switch.b"]
