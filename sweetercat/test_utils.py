from __future__ import division
import pytest
import pandas as pd
from utils import absolute_magnitude, plDensity, hz, readSC


def test_absolute_magnitude():
    m = 10
    assert isinstance(absolute_magnitude(1, 1), float)
    assert absolute_magnitude(1, m) > m
    assert absolute_magnitude(1, m) == 15
    assert absolute_magnitude(0.1, m) == m
    assert absolute_magnitude(0.01, m) < m
    assert absolute_magnitude(1/10, m) == m
    with pytest.raises(ZeroDivisionError):
        absolute_magnitude(0, m)


def test_plDensity():
    m, r = 1, 1
    assert isinstance(plDensity(m, r), float)
    assert round(plDensity(m, r), 2) == 1.33
    assert plDensity(0, r) == 0


def test_hz():
    df, _ = readSC()
    for (teff, logg, mass) in df.loc[:, ['teff', 'logg', 'mass']].values:
        lum = (teff/5777)**4 * (mass/((10**logg)/(10**4.44)))**2
        assert isinstance(hz(teff, lum, model=2), float)
        assert isinstance(hz(teff, lum, model=4), float)

    teff = 5777
    lum = 1
    for model in range(1, 6):
        assert isinstance(hz(teff, lum, model), float)
    results = [0.75, 0.98, 0.99, 1.71, 1.77]
    for model, result in enumerate(results, start=1):
        assert round(hz(teff, lum, model), 2) == result
    assert hz(teff, lum, 2) < hz(teff, lum, 4)  # hz1 < hz2


def test_readSC():
    df, plot_names = readSC()
    assert isinstance(df, pd.DataFrame)    #
    assert isinstance(plot_names, list)
    for name in plot_names:
        assert isinstance(name, str)
