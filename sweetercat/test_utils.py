from __future__ import division
from utils import absolute_magnitude, plDensity, hz


def test_absolute_magnitude():
    m = 10
    assert isinstance(absolute_magnitude(1, 1), float)
    assert absolute_magnitude(1, m) > m
    assert absolute_magnitude(1, m) == 15
    assert absolute_magnitude(0.1, m) == m
    assert absolute_magnitude(0.01, m) < m
    assert absolute_magnitude(1/10, m) == m


def test_plDensity():
    m, r = 1, 1
    assert isinstance(plDensity(m, r), float)
    assert round(plDensity(m, r), 2) == 1.33
    assert plDensity(0, r) == 0


def test_hz():
    teff = 5777
    lum = 1
    for model in range(1, 6):
        assert isinstance(hz(teff, lum, model), float)
    results = [0.75, 0.98, 0.99, 1.71, 1.77]
    for model, result in enumerate(results, start=1):
        assert round(hz(teff, lum, model), 2) == result
