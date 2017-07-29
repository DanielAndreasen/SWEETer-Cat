import pytest
import flask
from flask import url_for
from app import app as sc_app


# app fixture required for pytest-flask client
@pytest.fixture
def app():
    sc_app.testing = True
    sc_app.debug = True
    return sc_app


# First test using the client fixture from pytest-flask
def test_status_codes(client):
    for end_point in ('homepage', 'plot', 'publications'):
        print(end_point)
        assert client.get(url_for(end_point)).status_code == 200


# Need to check for 'stardetail' which also requires a star name.
@pytest.mark.xfail()  # VO table error
def test_stardetail_status_code(client):
    for star in ("KELT-20", "HD 202206", "BD+03 2562"):
        assert client.get(url_for("stardetail", star=star)).status_code == 200


@pytest.mark.xfail()  # VO table error
def test_plot_exo_status_code(client):
    assert client.get(url_for('plot_exo')).status_code == 200


@pytest.mark.xfail()  # BD+03  fails  "BD+03 2562" != "BD 03 2562"
def test_stardetail_request_path():
    for star in ["KELT-20", "HD 202206", "BD+03 2562"]:
        with sc_app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star


def test_request_paths():
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail'):
        with sc_app.test_request_context(path):
            assert flask.request.path == path
