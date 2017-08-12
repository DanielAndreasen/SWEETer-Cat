"""SWEETer-Cat tests regarding the plotting pages."""

import pytest
import numpy as np
from flask import url_for
from plot import check_scale, scaled_histogram


@pytest.fixture()
def form_data():
    """Default form values for testing."""
    form = {'color': 'Blue', 'x': 'teff', 'y': 'mass', 'z': 'Vmag',
            'x1': "None", 'x2': "None", 'y1': "None", 'y2': "None",
            'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}
    return form


@pytest.mark.parametrize("end_point", ["plot", "plot_exo"])
def test_plot_get_requests(client, end_point):
    """Test that all pages return status code: 200 using the end_points"""
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

        plot = client.post(url_for(end_point), data=form_data, follow_redirects=True)

        for feature in [title, xlabel, ylabel]:
            assert feature.encode("utf-8") in plot.data


def test_feh_with_log_scale(client, form_data):
    form_data["x"] = "feh"
    form_data["xscale"] = "log"

    plot = client.post(url_for('plot'), data=form_data, follow_redirects=True)
    # Just a random test so that the errors are raised at the moment.
    # Should add an assert for how the correct functionality should work.
    assert plot.status_code == 200


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


def test_redirect_on_wrong_xy(client, form_data):
    for dimension in ('z', 'y', 'x'):
        form_data[dimension] = 'wrong'
        plot = client.post(url_for('plot'), data=form_data, follow_redirects=True)
        assert plot.status_code == 200
        assert b"Select your settings:" in plot.data


def test_homogeneous_flag(client, form_data):
    form_data['checkboxes'] = 'homo'
    plot = client.post(url_for('plot'), data=form_data, follow_redirects=True)
    assert plot.status_code == 200
    assert b"Select your settings:" in plot.data


@pytest.mark.parametrize("url,column", [
    ("/plot/", "x"),
    ("/plot/", "y"),
    ("/plot-exo/", "z")
])
def test_plot_invalid_column_redirect(client, form_data, url, column):
    form_data[column] = "invalid_name"
    redirect_link = '<a href="{0}">{0}</a>'.format(url)

    plot = client.post(url, data=form_data, follow_redirects=False)
    assert plot.status_code == 302   # Redirection code
    assert b'Redirecting...' in plot.data
    assert redirect_link.encode("utf-8") in plot.data
