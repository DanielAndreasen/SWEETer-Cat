import pytest
import flask
from app import app


@pytest.mark.xfail()
def test_stardetail_request():
    for star in ["KELT-20", "HD 202206", "BD+03 2562"]:
        with app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star


def test_requests():
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail'):
        with app.test_request_context(path):
            assert flask.request.path == path
