from __future__ import division

import os

import numpy as np
import pandas as pd
import pytest

from utils import absolute_magnitude, hz, planetAndStar, plDensity, readSC
from utils import table_convert, stellar_radius, planetary_radius, get_default
from utils import luminosity, luminosity2


def test_absolute_magnitude():
    """Test the absolute_magnitude function."""
    m = 10
    assert isinstance(absolute_magnitude(1, 1), float)
    assert absolute_magnitude(1000, m) > m
    assert absolute_magnitude(1000, m) == 15
    assert absolute_magnitude(100, m) == m
    assert absolute_magnitude(1, m) < m
    assert absolute_magnitude(1 / 10, m) == -5
    with pytest.raises(ZeroDivisionError):
        absolute_magnitude(0, m)


def test_plDensity():
    """Test the plDensity function."""
    mass, radius = 1, 1
    assert isinstance(plDensity(mass, radius), float)
    assert round(plDensity(mass, radius), 2) == 1.33
    assert plDensity(0, radius) == 0
    with pytest.raises(ZeroDivisionError):
        plDensity(mass, 0)


def test_hz():
    """Test the hz function."""
    df, _ = readSC()
    for (teff, logg, mass) in df.loc[:, ['teff', 'logg', 'mass']].values:
        lum = (teff / 5777)**4 * (mass / ((10**logg) / (10**4.44)))**2
        assert isinstance(hz(teff, lum, model=2), float)
        assert isinstance(hz(teff, lum, model=4), float)

    teff = 5777
    lum = 1
    invalids = [{teff: lum}, [teff, lum], (teff, lum), "..."]
    for model in range(1, 6):
        assert isinstance(hz(teff, lum, model), float)
    results = [0.75, 0.98, 0.99, 1.71, 1.77]
    for model, result in enumerate(results, start=1):
        assert round(hz(teff, lum, model), 2) == result
        for invalid in invalids:
            assert np.isnan(hz(invalid, lum, model))
            assert np.isnan(hz(teff, invalid, model))
    assert hz(teff, lum, 2) < hz(teff, lum, 4)  # hz1 < hz2


def test_readSC():
    """Test the readSC function."""
    df, plot_names = readSC()
    assert isinstance(df, pd.DataFrame)
    assert isinstance(plot_names, list)
    for name in plot_names:
        assert isinstance(name, str)


def test_planetAndStar():
    """Test the planetAndStar function."""
    df, columns = planetAndStar()
    assert isinstance(df, pd.DataFrame)
    assert isinstance(columns, list)
    for column in columns:
        assert isinstance(column, str)


def test_readSC_with_nrows():
    """Test shortened readSC function."""
    for nrows in [2, 5]:
        df, plot_names = readSC(nrows=nrows)
        assert isinstance(df, pd.DataFrame)
        assert isinstance(plot_names, list)
        for name in plot_names:
            assert isinstance(name, str)
        assert len(df) == nrows


def test_table_convert():
    """Test the table_convert function."""
    for fmt in ['tsv', 'csv', 'hdf']:
        table_convert(fmt=fmt)
        fname = 'data/sweet-cat.{}'.format(fmt)
        assert os.path.isfile(fname)
        if fmt != 'tsv':
            os.remove(fname)
    with pytest.raises(NotImplementedError):
        table_convert('fits')


def test_stellar_radius():
    mass, logg = 1, 4.44
    assert isinstance(stellar_radius(mass, logg), float)
    assert stellar_radius(mass, logg) == 1
    assert stellar_radius(0, logg) == 0
    with pytest.raises(TypeError):
        stellar_radius('...', logg)
    with pytest.raises(TypeError):
        stellar_radius(mass, '...')
    with pytest.raises(ValueError):
        stellar_radius(-1, logg)


def test_planetary_radius():
    mass, radius = 1, 1
    assert isinstance(planetary_radius(mass, radius), (int, float))
    assert planetary_radius(mass, radius) == radius
    assert planetary_radius('...', radius) == radius
    assert planetary_radius(0, '...') == 0
    assert planetary_radius('...', '...') == '...'
    assert round(planetary_radius(1, '...'), 2) == 1
    assert round(planetary_radius(0.2, '...'), 2) == 5.33
    with pytest.raises(ValueError):
        planetary_radius(-1, radius)


def test_get_default():
    value = 42
    assert get_default(value, 1, int) == value
    assert get_default(value, 'hello', str) == 'hello'
    assert isinstance(get_default(value, 1, int), int)
    assert isinstance(get_default(value, 'hello', str), str)
    assert get_default('...', 42, str) == 42
    assert get_default('---', 42, str, na_value='---') == 42
    assert isinstance(get_default('---', 42, str, na_value='---'), int)


def test_luminosity():
    mass, teff, logg = 1.3, 4554, 4.32
    assert luminosity(1, 5777, 4.44) == 1
    assert isinstance(luminosity(mass, teff, logg), (int, float))
    assert luminosity(0, teff, logg) == 0
    assert luminosity(mass, 0, logg) == 0
    assert luminosity(mass, teff, 0) != 0


def test_luminosity2():
    p, m = 10, 10
    ps = 1/4.848136811133344e-09
    ms = -26.74
    assert isinstance(luminosity2(p, m), (int, float))
    assert luminosity2(ps, ms) == 1
    assert round(luminosity2(p, m), 3) == 0.857
    assert int(luminosity2(p, 0)) == 8567
    with pytest.raises(ZeroDivisionError):
        luminosity2(0, m)
    with pytest.raises(TypeError):
        luminosity2(p, 'm')
