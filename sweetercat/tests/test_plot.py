"""SWEETer-Cat tests regarding the plotting pages."""

import pytest
from flask import url_for


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


def test_title_and_axis_labels(client):
    for xname, yname in zip(("teff", "vt", "par"), ("mass", "Vabs", "logg")):
        # test_data = {'color': 'Blue', 'x': xname, 'y': yname, 'z': 'Vmag',
        #          'x1':  "None", 'x2':  "None", 'y1':  "None", 'y2': "None",
        #          'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}
        print(xname, yname)
        test_data = {'color': 'Blue', 'x': xname, 'y': yname, 'z': 'Vmag',
                     'x1': "", 'x2': "", 'y1': "", 'y2': "",
                     'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}

        title = '"text":"{0} vs. {1}:'.format(xname, yname)
        xlabel = '"axis_label":"{0}"'.format(xname)
        ylabel = '"axis_label":"{0}"'.format(yname)

        for end_point in ('plot',):  # 'plot_exo'
            plot = client.post(url_for(end_point), data=test_data, follow_redirects=True)
            print(plot)
            for feature in [title, xlabel, ylabel]:
                assert feature.encode("utf-8") in plot.data


def test_feh_with_log_scale(client):
    test_data = {'color': 'Blue', 'x': "feh", 'y': "feh", 'z': 'Vmag',
                 'x1': "None", 'x2': "None", 'y1': "None", 'y2': "None",
                 'xscale': 'linear', 'yscale': 'log', 'checkboxes': ''}

    for end_point in ('plot',):  # 'plot_exo'
        plot = client.post(url_for(end_point), data=test_data, follow_redirects=True)
        assert plot.status_code == 200
