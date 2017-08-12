"""SWEETer-Cat tests regarding the plotting pages."""

import numpy as np
import pytest
from flask import url_for

from plot import count, extract, get_limits, scaled_histogram


def test_plot_get_requests(client):
    """Test that all pages return status code: 200 using the end_points"""
    for end_point in ('plot', 'plot_exo'):
        plot = client.get(url_for(end_point))

        assert plot.status_code == 200
        assert b"Select your settings:" in plot.data


def test_plot_post_request(client):
    test_data = {'color': 'Blue', 'x': 'teff', 'y': 'mass', 'z': 'Vmag',
                 'x1': 8000, 'x2': 2500, 'y1': 0, 'y2': 5,
                 'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}

    for end_point in ('plot',):  # 'plot_exo'
        plot = client.post(url_for(end_point), data=test_data, follow_redirects=True)

        assert plot.status_code == 200
        assert b"Select your settings:" in plot.data


def test_post_z_none_43(client):
    """Test that setting z to None does not produce an error."""
    test_data = {"color": "Blue", "x": "teff", "y": "mass", "z": "None",
                 "x1": 8000, "x2": 2500, "y1": 0, "y2": 5,
                 "xscale": "linear", "yscale": "log", "checkboxes": ""}

    for end_point in ("plot", "plot_exo"):
        plot = client.post(url_for(end_point), data=test_data, follow_redirects=True)

        assert plot.status_code == 200
        assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("points,expected_bins", [
    (0, 5),
    (299, 5),
    (300, 6),
    (2000, 40),
])
def test_scaled_histogram_bin_number(points, expected_bins):
    for scale in ("linear", "log"):
        data = np.random.rand(points)
        hist, edges, hmax = scaled_histogram(data, points, scale)

        assert len(hist) == expected_bins
        assert len(hist) + 1 == len(edges)
        assert np.all(hist <= hmax)


def test_get_limits():
    x = range(5)
    y = range(5, 10)
    request_form = {"x1": 1, "x2": "two", "y1": "", "y2": [4]}
    limits = get_limits(request_form, x, y)
    assert limits == [1., 4., 5., 9.]
    for lim in limits:
        assert isinstance(lim, (float, int))


def test_count():
    x = np.arange(20)
    y = np.arange(5, 25)
    number = count(x, y, [1, 11], [10, 20])
    assert number == 5
    assert isinstance(number, int)


@pytest.mark.parametrize("limit,error", [
    ([], ValueError),
    ([1], ValueError),
    ([1, 2, 3], ValueError),
    ("[1,2]", TypeError),
    ((1, 2), TypeError)
])
def test_count_limit_errors(limit, error):
    x = range(20)
    y = range(5, 26)
    with pytest.raises(error):
        count(x, y, [3, 8], limit)
    with pytest.raises(error):
        count(x, y, limit, [10, 15])


@pytest.mark.parametrize("endpoint,x,y,z", [
    ("plot", "par", "feh", None),
    ("plot", "Vabs", "mass", "teff"),
    ("plot_exo", "plMass", "plDensity", None),
    ("plot_exo", "mag_v", "b", "teff"),
])
def test_plot_extraction(SCdata, planetStardata, endpoint, x, y, z):

    if endpoint == 'plot_exo':
        df, _ = planetStardata
    else:
        df, _ = SCdata

    df1, x1, y1, z1 = extract(df, x, y, z, [])
    df2, x2, y2, z2 = extract(df, x, y, z, ["homo"])

    assert len(df.columns) > 5
    assert len(df1.columns) <= 5
    assert len(df2.columns) <= 5

    assert not all(df1["flag"])
    assert all(df2["flag"])

    if z is None:
        assert z1 is None and z2 is None
    else:
        assert len(z1) > len(z2)
    assert len(x1) > len(x2)
    assert len(y1) > len(y2)

    assert all([name in df1.columns for name in ["Star", x, y, z, "flag"]
                if name is not None])
    assert all([name in df2.columns for name in ["Star", x, y, z, "flag"]
                if name is not None])
