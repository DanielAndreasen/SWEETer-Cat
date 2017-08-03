from __future__ import division
import os
import pytest
import numpy as np
import pandas as pd
from utils import absolute_magnitude, plDensity, hz, readSC, planetAndStar, table_convert


def test_absolute_magnitude():
    """Test the absolute_magnitude function"""
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
    """Test the plDensity function"""
    m, r = 1, 1
    assert isinstance(plDensity(m, r), float)
    assert round(plDensity(m, r), 2) == 1.33
    assert plDensity(0, r) == 0
    with pytest.raises(ZeroDivisionError):
        plDensity(m, 0)


def test_hz():
    """Test the hz function"""
    df, _ = readSC()
    for (teff, logg, mass) in df.loc[:, ['teff', 'logg', 'mass']].values:
        lum = (teff/5777)**4 * (mass/((10**logg)/(10**4.44)))**2
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
    """Test the readSC function"""
    df, plot_names = readSC()
    assert isinstance(df, pd.DataFrame)
    assert isinstance(plot_names, list)
    for name in plot_names:
        assert isinstance(name, str)


def test_planetAndStar():
    """Test the planetAndStar function"""
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
    """Test the table_convert function"""
    for fmt in ['tsv', 'csv', 'hdf']:
        table_convert(fmt=fmt)
        fname = 'data/sweet-cat.{}'.format(fmt)
        assert os.path.isfile(fname)
        if fmt != 'tsv':
            os.remove(fname)
    with pytest.raises(NotImplementedError):
        table_convert('fits')
