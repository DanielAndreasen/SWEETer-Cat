"""SWEETer-Cat tests regarding the plotting pages."""

import numpy as np
import pytest
from flask import url_for
<<<<<<< HEAD
from plot import get_limits, scaled_histogram, count
=======
>>>>>>> master

from plot import check_scale, scaled_histogram

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


@pytest.fixture()
def form_data():
    """Default form values for testing."""
    form = {'color': 'Blue', 'x': 'teff', 'y': 'mass', 'z': 'Vmag',
            'x1': "None", 'x2': "None", 'y1': "None", 'y2': "None",
            'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}
    return form


@pytest.mark.parametrize("end_point", ["plot", "plot_exo"])
def test_plot_get_requests(client, end_point):
    """Test that all pages return status code: 200 using the end_points."""
    plot = client.get(url_for(end_point))

    assert plot.status_code == 200
    assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("end_point", ["plot", "plot_exo"])
def test_plot_post_request(client, form_data, end_point):
    plot = client.post(url_for(end_point), data=form_data, follow_redirects=False)
    assert plot.status_code == 200
    assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("end_point", ["plot", "plot_exo"])
def test_post_z_none_43(client, form_data, end_point):
    """Test that setting z to None does not produce an error."""
    form_data["z"] = "None"

    plot = client.post(url_for(end_point), data=form_data, follow_redirects=False)
    assert plot.status_code == 200
    assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("end_point", ["plot", "plot_exo"])
def test_title_and_axis_labels(client, form_data, end_point):
    for xname, yname in zip(("teff", "vt", "par"), ("mass", "Vabs", "logg")):
        form_data["x"], form_data["y"], form_data["yscale"] = xname, yname, "log"
        title = '"text":"{0} vs. {1}:'.format(xname, yname)
        xlabel = '"axis_label":"{0}"'.format(xname)
        ylabel = '"axis_label":"{0}"'.format(yname)

        plot = client.post(url_for(end_point), data=form_data, follow_redirects=False)

        for feature in [title, xlabel, ylabel]:
            assert feature.encode("utf-8") in plot.data


@pytest.mark.parametrize("dimension", ["x", "y"])
def test_feh_with_log_scale(client, form_data, dimension):
    form_data[dimension] = "feh"
    form_data["{}scale".format(dimension)] = "log"

    plot = client.post(url_for('plot'), data=form_data, follow_redirects=False)

    assert b'Scale was changed from log to linear' in plot.data


@pytest.mark.parametrize("x,y,xs,ys,xs_expected,ys_expected,error", [
    (range(5), range(5), 'linear', 'linear', 'linear', 'linear', None),
    (range(5), range(5), 'log', 'log', 'linear', 'linear', True),
    (range(1, 5), range(1, 5), 'log', 'log', 'log', 'log', None),
    (range(1, 5), range(1, 5), 'linear', 'linear', 'linear', 'linear', None),
    (range(-5, -1), range(-5, -1), 'linear', 'log', 'linear', 'linear', True),
])
def test_check_scale(x, y, xs, ys, xs_expected, ys_expected, error):
    xscale, yscale, err = check_scale(x, y, xs, ys)
    assert xscale == xs_expected
    assert yscale == ys_expected
    assert err == error


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


<<<<<<< HEAD
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
=======
def test_homogeneous_flag(client, form_data):
    form_data['checkboxes'] = 'homo'
    plot = client.post(url_for('plot'), data=form_data, follow_redirects=False)
    assert plot.status_code == 200
    assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("endpoint,dimension", [
    ("plot", "x"),
    ("plot", "y"),
    ("plot_exo", "z")
])
def test_redirect_on_wrong_xyz(client, form_data, endpoint, dimension):
    form_data[dimension] = "wrong"

    plot = client.post(url_for(endpoint), data=form_data, follow_redirects=False)
    redirected_plot = client.post(url_for(endpoint), data=form_data, follow_redirects=True)

    assert plot.status_code == 302   # Redirection code
    assert b'Redirecting...' in plot.data
    assert urlparse(plot.location).path == url_for(endpoint)  # redirect location

    assert redirected_plot.status_code == 200
    assert b"Select your settings:" in redirected_plot.data
>>>>>>> master
