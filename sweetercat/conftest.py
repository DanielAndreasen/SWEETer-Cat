"""Conftest is for fixtures that will run in all test files."""
import json

import pytest
from flask import url_for

from app import app as sc_app
from utils import planetAndStar, readSC


@pytest.fixture
def app():
    sc_app.testing = True
    sc_app.debug = True
    return sc_app


@pytest.fixture
def SCdata():
    """SWEET-Cat database fixture."""
    return readSC()


@pytest.fixture
def planetStardata():
    """SWEET-Cat + ExoplanetEU + database fixture."""
    return planetAndStar()


@pytest.fixture
def publication_response(client):
    return client.get(url_for("publications"))


@pytest.fixture
def publication_data():
    """Load publication data file."""
    with open('data/publications.json') as pubs:
        pubs = json.load(pubs)
    return pubs

@pytest.fixture(scope="module",
                params=["Not a Star", "None"])
def bad_starname(request):
    return request.param


@pytest.fixture(scope="module",
                params=["", None])
def invalid_starname(request):
    return request.param
