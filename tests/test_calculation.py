import math
import pytest


def test_sum_and_average(code):
    _, calc = code
    assert calc.combine('power', [10.513, 1.556]) == pytest.approx(12.069)
    assert calc.combine('voltage', [235.272, 235.302]) == pytest.approx(235.287)
    assert calc.combine('current', [0.141, 0.018]) == pytest.approx(0.159)
    assert calc.combine('energy', [49.750829, .579417]) == pytest.approx(50.330246)
    assert calc.combine('frequency', [50.005, 50.065]) == pytest.approx(50.035)


def test_normalize_units(code):
    _, calc = code
    assert calc.normalize('power','1.5','kW') == 1500
    assert calc.normalize('energy','1234','Wh') == 1.234
    assert calc.normalize('current','150','mA') == .15
    assert calc.normalize('voltage','235000','mV') == 235
    assert calc.normalize('power_factor','0.91','') == 91
    assert calc.normalize('power_factor','91','%') == 91
    assert calc.normalize('power_factor','0.9',None) == 90
    assert calc.normalize('power','1.5','kWh') is None
    assert calc.normalize('power','unknown','W') is None
    assert calc.normalize('power','nan','W') is None
    assert calc.normalize('power',math.inf,'W') is None


def test_weighted_pf_and_bad_values(code):
    _, calc = code
    assert calc.combine('power_factor', [80, 100], [3,1]) == 85
    assert calc.combine('power_factor', [80, 100]) == 90
    assert calc.combine('power_factor', [80,100],[0,0]) == 90
    assert calc.combine('power', [1]) is None
    assert calc.combine('power', [1, math.inf]) is None
