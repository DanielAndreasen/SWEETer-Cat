import os

import flask
import pytest
from flask import escape, url_for

from app import app as sc_app

try:  # pragma: no cover
    from urllib.parse import urlparse  # pragma: no cover
except ImportError:  # pragma: no cover
    from urlparse import urlparse  # pragma: no cover


def test_homepage_status_code(client):
    homepage = client.get(url_for("homepage"))
    assert homepage.status_code == 200

    # Link to SWEET-Cat
    assert b'<a href="https://www.astro.up.pt/resources/sweet-cat/">SWEET-Cat</a>' in homepage.data


def test_parameter_description_on_homepage(client):
    homepage = client.get(url_for("homepage"))
    assert b"/static/table.pdf" in homepage.data
    assert b"A detailed description of each field can be found"in homepage.data

    table = client.get("/static/table.pdf")
    assert table.status_code == 200
    assert b"<dc:format>application/pdf</dc:format>\n" in table.data


# Need to check for 'stardetail' which also requires a star name.
def test_stardetail_status_code(client, SCdata, planetStardata):
    """Test stardetail will return status code: 200 when submitted with star."""
    # Passing in planetStardata moves the setup time (~4.8s) of the
    # caching etc into the fixture, which can be shared between tests
    df, _ = SCdata
    df = df.sample(5)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        print("Testing {}".format(star))   # Catch star name if test fails.
        assert client.get(url_for("stardetail", star=star)).status_code == 200
        print("{} passed".format(star))


def test_bad_starname(client, bad_starname):
    bad_star = client.get(url_for("stardetail", star=bad_starname),
                          follow_redirects=False)
    assert bad_star.status_code == 302
    # redirects to homepage
    assert urlparse(bad_star.location).path == url_for("homepage")


@pytest.mark.xfail(reason='None is not allowed to pass to the function')
def test_invalid_starname(client, invalid_starname):
    print(invalid_starname)
    invalid_star = client.get(url_for("stardetail", star=invalid_starname),
                              follow_redirects=False)
    # Error 404, which gives here a status code 200 (404 page exists)
    assert invalid_star.status_code == 200


def test_stardetail_request_path(SCdata):
    """Test that the stardetail renders properly."""
    df, _ = SCdata
    df = df.sample(5)
    stars = df.Star.values
    for star in stars:
        print("Testing {}".format(star))
        # BD+ stars have replaced it with a space. Not a problem in app since
        # the stardetail show up with planets
        star = star.replace('+', ' ')
        with sc_app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star
        print("{} Passed".format(star))


def test_request_paths():
    """Test the different URL paths return the right path."""
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail', '/static/table.pdf'):
        with sc_app.test_request_context(path):
            assert flask.request.path == path


def test_publication_response_status_code(publication_response):
    assert publication_response.status_code == 200


@pytest.mark.parametrize("heading", [
    b"Main papers", b"Derived papers", b"Authors:", b"Abstract:", b"read more"])
def test_publication_page_headings(publication_response, heading):
    """Test for the labels Abstact:, Authors: etc."""
    assert heading in publication_response.data


@pytest.mark.parametrize("category", ["main", "other"])
def test_publication_titles(publication_response, publication_data, category):
    """Test all the plublication titles are present."""
    for paper in publication_data[category]:
        title = escape(paper["title"]).encode('utf-8')
        assert title in publication_response.data


@pytest.mark.parametrize("category", ["main", "other"])
def test_publication_links(publication_response, publication_data, category):
    """Test all the plublication adsabs links are present.

    Test that links are inserted for the title and "read more" sections.
    """
    for paper in publication_data[category]:
        url = escape(paper["adsabs"])
        read_more = '...<a href="{0}" target="_blank"> read more</a>'.format(url)
        title_link = '<a href="{0}" target="_blank">{1}</a>'.format(url, paper["title"])
        assert read_more.encode('utf-8') in publication_response.data
        assert title_link.encode('utf-8') in publication_response.data


@pytest.mark.parametrize("category", ["main", "other"])
def test_publication_authors(publication_response, publication_data, category):
    """Test all the plublication authors are present."""
    for paper in publication_data[category]:
        authors = escape(paper["authors"]).encode('utf-8')
        assert authors in publication_response.data


@pytest.mark.parametrize("category", ["main", "other"])
def test_publication_abstracts(publication_response, publication_data, category):
    """Test all the plublication abstracts are present."""
    abstract_limit = 480   # characters to compare
    for paper in publication_data[category]:
        abstract = paper["abstract"][:abstract_limit].encode('utf-8')
        assert abstract in publication_response.data


def test_stardetail_template_text(client, SCdata):
    """Test that that text on the stardetails are returned.

    (Maybe a bit overboard)
    """
    sttext = ["General info", "Reference article:", "Right ascension:", "Declination:",
              "Magnitude:", "Parallax:", "mas", "Atmospheric parameters", "Teff:", "K",
              "logg:", "[Fe/H]:", "dex", "vt:", "km/s", "Other info", "Mass:"]
    df, _ = SCdata
    d0 = df[df.Star == 'Kepler-617']
    d1 = df[df.Star == 'Kepler-444']
    df = df.sample(3)
    df = df.append([d0, d1])

    stars = df.Star

    for i, star in stars.iteritems():
        print("Test {}: {}".format(i, star))
        star_detail = client.get(url_for("stardetail", star=star))

        if df["flag"][i]:
            assert b"Parameters analysed by the Porto group" in star_detail.data
        else:
            assert b"Parameters from the literature" in star_detail.data
        for text in sttext:
            assert text.encode("utf-8") in star_detail.data
        print("{0} Passed".format(star))


def test_download_status_code(client):
    # Download database on-hand
    assert os.path.isfile('data/sweet-cat.tsv')
    assert client.get(url_for('download', fname='sweet-cat.tsv')).status_code == 200

    # Download with format conversion
    for fmt in ('csv', 'hdf'):
        fname = 'sweet-cat.{}'.format(fmt)
        assert client.get(url_for('download', fname=fname)).status_code == 200
        assert not os.path.isfile('data/{}'.format(fname))

    # Invlaid format but goes to the 404 page
    assert client.get(url_for('download', fname='sweet-cat.fits')).status_code == 200


def test_download_other(client):
    fname = 'requirements.txt'
    c = client.get(url_for('download', fname=fname))
    assert c.status_code == 200
    assert os.path.isfile('data/{}'.format(fname))


def test_error_404(client):
    """Test the 404 response of an invalid url."""
    error404 = client.get('/invalid_url')

    assert b'This page could not be found' in error404.data
    assert b'Our space monkeys are working on the issue...' in error404.data
    assert b'<img src="/static/spacemonkey.png" alt="">' in error404.data


def test_issue54_rounding(client):
    """Check that the troublesome values are removed."""
    homepage = client.get(url_for("homepage"))
    for number in ['4.34399999999999', '14.386']:
        assert number.encode('utf-8') not in homepage.data


def test_table_is_clean(client):
    homepage = client.get(url_for("homepage"))
    assert b'NaN' not in homepage.data
    # "..." is not null so "..."[:-2] -> .
    assert b'<td style="white-space:nowrap;">.</td>' not in homepage.data


def test_about_page(client):
    c = client.get(url_for('about'))
    assert c.status_code == 200
    assert b'open an issue on Github' in c.data


def test_local_page(client):
    c = client.get(url_for('local'))
    assert c.status_code == 200
    assert b'Combining the data' in c.data


def test_mpld3_status_code(client):
    c = client.get(url_for('mpld3_plot'))
    assert c.status_code == 200


def test_stardetail_no_sma(client, planetStardata):
    """Test stardetail will return status code: 200 when submitted with planet
    without known SMA."""
    df, _ = planetStardata
    df = df[df.sma.isnull()]
    d0 = df[df.Star == 'Kepler-154']
    df = df.sample(2)
    df = df.append(d0)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        print("Testing {}".format(star))   # Catch star name if test fails.
        assert client.get(url_for("stardetail", star=star)).status_code == 200
        print("{} passed".format(star))


def test_stardetail_inside_hz(client, planetStardata):
    """Test stardetail will return status code: 200 when submitted with planet
    without known SMA."""
    df, _ = planetStardata
    # GJ 581 has a star before, inside, and after the HZ
    d0 = df[df.Star == 'GJ 581']
    df = df.sample(2)
    df = df.append(d0)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        print("Testing {}".format(star))   # Catch star name if test fails.
        assert client.get(url_for("stardetail", star=star)).status_code == 200
        print("{} passed".format(star))


def test_stardetail_no_planets(client, planetStardata):
    """Test stardetail will return status code: 200 when submitted with planet
    without known SMA."""
    df, _ = planetStardata
    # GJ 581 has a star before, inside, and after the HZ
    d0 = df[df.Star == 'GJ 667C']
    df = df.sample(2)
    df = df.append(d0)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        print("Testing {}".format(star))   # Catch star name if test fails.
        assert client.get(url_for("stardetail", star=star)).status_code == 200
        print("{} passed".format(star))
