"""Pure helpers for renamed source entities."""


def test_replace_entity_id_keeps_order(code):
    _, calc = code
    assert calc.replace_entity_id(["switch.a", "switch.b"], "switch.b", "switch.c") == ["switch.a", "switch.c"]


def test_replace_entity_id_ignores_unknown(code):
    _, calc = code
    assert calc.replace_entity_id(["switch.a", "switch.b"], "switch.x", "switch.y") == ["switch.a", "switch.b"]
