"""Conftest is for fixtures that will run in all test files."""
import pytest
from app import app as sc_app


@pytest.fixture
def app():
    sc_app.testing = True
    sc_app.debug = True
    return sc_app
