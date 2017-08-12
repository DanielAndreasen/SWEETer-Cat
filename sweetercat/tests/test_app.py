import os
import json
import flask
from flask import url_for
from app import app as sc_app


def test_homepage(client, SCdata):
    homepage = client.get(url_for("homepage"))
    assert homepage.status_code == 200

    # Link to SwEEt-Cat
    assert b'<a href="https://www.astro.up.pt/resources/sweet-cat/">SWEET-Cat</a>' in homepage.data

    # Table column names
    __, cols = SCdata
    for col in cols:
        header = "<th>{0}</th>".format(col)
        print(header)
        if col in ["Vabs"]:
            assert header.encode('utf-8') not in homepage.data
        else:
            assert header.encode('utf-8') in homepage.data


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
    # Passing in planetStardata moves the setup time (~4.8s) of the caching etc into the fixture, which can be shared between tests.
    df, _ = SCdata
    df = df.sample(5)
    # All stars are a slow test
    stars = df.Star.values
    for star in stars:
        print(star)   # Catch star name if test fails.
        assert client.get(url_for("stardetail", star=star)).status_code == 200


def test_stardetail_request_path(SCdata):
    """Test that the stardetail renders properly."""
    df, _ = SCdata
    df = df.sample(50)
    stars = df.Star.values
    for star in stars:
        print(star)
        # BD+ stars have replaced it with a space. Not a problem in app since
        # the stardetail show up with planets
        star = star.replace('+', ' ')
        with sc_app.test_request_context('/stardetail/?star={}'.format(star)):
            assert flask.request.path == '/stardetail/'
            assert flask.request.args['star'] == star


def test_request_paths():
    """Test the different URL paths return the right path"""
    for path in ('/', '/plot/', '/plot-exo/', '/publications/', '/stardetail', '/static/table.pdf'):
        with sc_app.test_request_context(path):
            assert flask.request.path == path


def test_publication_headings(client):
    """Test for the labels Abstact:, Authors: etc."""
    publications = client.get(url_for("publications"))
    for heading in [b"Main papers", b"Derived papers", b"Authors:", b"Abstract:", b"read more"]:
        assert heading in publications.data


def test_publication_response_data(client):
    """Test all the plublication data is present.

    Test that links are inserted for the title and "read more" sections.
    """
    publications = client.get(url_for("publications"))
    assert publications.status_code == 200

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
                    assert title_link in publications.data
                    assert read_more in publications.data
                elif "abstract" in key:
                    assert value[:480] in publications.data
                else:
                    assert value in publications.data


def test_stardetail_template_text(client, SCdata):
    """Test that that text on the stardetails are returned.

    (Maybe a bit overboard)
    """
    sttext = ["General info", "Reference article:", "Right ascension:", "Declination:",
              "Magnitude:", "Parallax:", "mas", "Atmospheric parameters", "Teff:", "K",
              "logg:", "[Fe/H]:", "dex", "vt:", "km/s", "Other info", "Mass:"]
    # pltext = ["Planetary information", "Mass", "MJup", "Radius", "RJup", "Density",
    #           "Orbital parameters", "Period:", "days", "Semi-major axis:", "AU",
    #           "Inner habitable zone limit:", "Density", "Outer habitable zone limit:"]
    df, _ = SCdata
    df = df.sample(5)
    stars = df.Star

    for i, star in stars.iteritems():
        star_detail = client.get(url_for("stardetail", star=star))

        if df["flag"][i]:
            assert b"Parameters analysed by the Porto group" in star_detail.data
        else:
            assert b"Parameters from the literature" in star_detail.data
        for text in sttext:
            assert text.encode("utf-8") in star_detail.data

    # if (star has planet parameters): # Need planetandStar instead of readSC
    # for text in pltext:
    #     assert text.encode("utf-8") in star_detail.data


def test_download_status_code(client):
    # Download database on-hand
    assert os.path.isfile('data/sweet-cat.tsv')
    assert client.get(url_for('download', fname='sweet-cat.tsv')).status_code == 200

    # Download with format conversion
    for fmt in ('csv', 'hdf'):
        fname = 'sweet-cat.{}'.format(fmt)
        assert client.get(url_for('download', fname=fname)).status_code == 200
        assert not os.path.isfile('data/{}'.format(fname))

    # Invlaid format
    assert client.get(url_for('download', fname='sweet-cat.fits')).status_code == 302


def test_error_404(client):
    """Test the 404 response of an invalid url."""
    error404 = client.get('/invalid_url')

    assert b'This page could not be found' in error404.data
    assert b'Our space monkeys are working on the issue...' in error404.data
    assert b'<img src="static/spacemonkey.png" alt="">' in error404.data


def test_issue54_rounding(client):
    """Check that the troublesome values are removed."""
    homepage = client.get(url_for("homepage"))
    for number in ['4.34399999999999', '14.386']:
        assert number.encode('utf-8') not in homepage.data
