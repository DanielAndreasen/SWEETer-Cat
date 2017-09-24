"""Conftest is for fixtures that will run in all test files."""
import json
import pytest
from app import app as sc_app
from utils import readSC, planetAndStar


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
    """SWEET-Cat + ExoplanetEU +  database fixture."""
    return planetAndStar()


@pytest.fixture()
def publication_data():
    """Load publication data file."""
    with open('data/publications.json') as pubs:
        pubs = json.load(pubs)
    return pubs
