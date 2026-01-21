"""Pytest configuration and fixtures for API tests."""
import pytest
import os

# Set the app directory before importing
os.environ.setdefault('APP_DATA_DIR', '/tmp/anime1-test')

from src.app import create_app
from src.models.database import init_database, close_database

# Exclude integration test scripts that have module-level code
# These require special setup (build artifacts, running app, etc.)
collect_ignore_glob = [
    "integration/*",
]


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    yield app


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    with app.test_client() as client:
        yield client
