import pytest
import flask
import json
from flask import url_for
from app import app as sc_app
from utils import readSC


# app fixture required for pytest-flask client
@pytest.fixture
def app():
    sc_app.testing = True
    sc_app.debug = True
    return sc_app


# First test using the client fixture from pytest-flask
def test_status_codes(client):
    for end_point in ('homepage', 'plot', 'publications', 'plot_exo'):
        assert client.get(url_for(end_point)).status_code == 200


# Need to check for 'stardetail' which also requires a star name.
def test_stardetail_status_code(client):
    df, _ = readSC()
    # All stars are a slow test
    stars = df['Star'].values[:5]
    for star in stars:
        assert client.get(url_for("stardetail", star=star)).status_code == 200


def test_stardetail_request_path():
    df, _ = readSC()
    stars = df.Star.values
    for star in stars:
        # BD+ stars have replaced it with a space. Not a problem in app since
        # the stardetail show up with planets
        star = star.replace('+', ' ')
        with sc_app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star


def test_request_paths():
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail'):
        with sc_app.test_request_context(path):
            assert flask.request.path == path


def test_publication_headings(client):
    """ Test for the labels Abstact:, Authors: etc.
    """
    response = client.get(url_for("publications"))
    for heading in [b"Main papers", b"Derived papers", b"Authors:", b"Abstract:", b"read more"]:
        assert heading in response.data


def test_publication_response_data(client):
    """Test all the plublication data is present.

    Test that links are inserted for the title and "read more" sections.
    """
    response = client.get(url_for("publications"))
    with open('publications.json') as pubs:
        pubs = json.load(pubs)
    for paper_key in pubs:
        for paper in pubs[paper_key]:
            for key, value in paper.items():
                value = value.encode('utf-8')
                if "adsabs" in key:
                    url = paper["adsabs"].replace("&", "&amp;")
                    read_more = '...<a href="{0}" target="_blank"> read more</a>'.format(url).encode('utf-8')
                    title_link = '<a href="{0}" target="_blank">{1}</a>'.format(url, paper["title"]).encode('utf-8')
                    assert title_link in response.data
                    assert read_more in response.data
                elif "abstract" in key:
                    assert value[:480] in response.data
                else:
                    assert value in response.data

