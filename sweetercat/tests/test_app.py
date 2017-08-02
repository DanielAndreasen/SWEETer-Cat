import pytest
import flask
import os
import json
from utils import readSC
from flask import url_for
from app import app as sc_app


# app fixture required for pytest-flask client
@pytest.fixture
def app():
    sc_app.testing = True
    sc_app.debug = True
    return sc_app


def test_status_codes(client):
    """Test that all pages return status code: 200 using the end_points"""
    for end_point in ('homepage', 'plot', 'publications', 'plot_exo'):
        assert client.get(url_for(end_point)).status_code == 200


def test_plot_POST_z_None(client):
    """Test that setting z to None does not error."""

    # POST request
    for end_point in ('plot', "plot_exo"):
        test_data = {'color': "Blue", 'x': "teff", 'y': "mass", 'z': "None",
                     'xscale': "linear", 'yscale': "log",
                     'x1': 8000, 'x2': 2500,
                     'y1': 0, 'y2': 5,
                     'checkboxes': ""}
        plot = client.post(url_for(end_point), data=test_data, follow_redirects=True)
        print(plot.data)
        assert plot.status_code == 200


# Need to check for 'stardetail' which also requires a star name.
def test_stardetail_status_code(client):
    """Test stardetail will return status code: 200 when submitted with star"""
    df, _ = readSC(nrows=5)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        assert client.get(url_for("stardetail", star=star)).status_code == 200


def test_stardetail_request_path():
    """Test that the stardetail renders properly"""
    df, _ = readSC(nrows=50)
    stars = df.Star.values
    for star in stars:
        # BD+ stars have replaced it with a space. Not a problem in app since
        # the stardetail show up with planets
        star = star.replace('+', ' ')
        with sc_app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star


def test_request_paths():
    """Test the different URL paths return the right path"""
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail'):
        with sc_app.test_request_context(path):
            assert flask.request.path == path


def test_publication_headings(client):
    """ Test for the labels Abstact:, Authors: etc."""
    response = client.get(url_for("publications"))
    for heading in [b"Main papers", b"Derived papers", b"Authors:", b"Abstract:", b"read more"]:
        assert heading in response.data


def test_publication_response_data(client):
    """Test all the plublication data is present.

    Test that links are inserted for the title and "read more" sections.
    """
    response = client.get(url_for("publications"))
    with open('data/publications.json') as pubs:
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


def test_stardetail_template_text(client):
    """Test that that text on the stardetails are returned.

    (Maybe a bit overboard)
    """
    sttext = ["General info", "Reference article:", "Right ascension:", "Declination:",
                "Magnitude:", "Parallax:", "mas", "Atmospheric parameters", "Teff:", "K",
                "logg:", "[Fe/H]:", "dex", "vt:", "km/s", "Other info", "Mass:"]
    pltext = ["Planetary information", "Mass", "MJup", "Radius", "RJup", "Density",
                 "Orbital parameters", "Period:", "days", "Semi-major axis:", "AU",
                 "Inner habitable zone limit:", "Density", "Outer habitable zone limit:"]
    df, __ = readSC(nrows=10)
    stars = df.Star.values
    for i, star in enumerate(stars):
        response = client.get(url_for("stardetail", star=star))
        if df["flag"][i]:
            assert b"Parameters analysed by the Porto group" in response.data
        else:
            assert b"Parameters from the literature" in response.data
        for text in sttext:
            assert text.encode("utf-8") in response.data

    # if (star has planet parameters): # Need planetandStar instead of readSC
    # for text in pltext:
    #     assert text.encode("utf-8") in response.data


def test_download_status_code(client):
    for fmt in ('csv', 'hdf'):
        fname = 'sweet-cat.{}'.format(fmt)
        assert client.get(url_for('download', fname=fname)).status_code == 200
        assert not os.path.isfile('data/{}'.format(fname))
    assert client.get(url_for('download', fname='sweet-cat.tsv')).status_code == 200
    assert os.path.isfile('data/sweet-cat.tsv')
    assert client.get(url_for('download', fname='sweet-cat.fits')).status_code == 302
