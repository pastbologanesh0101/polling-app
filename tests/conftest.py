import os

import pytest

from app import create_app


@pytest.fixture
def app():
    flask_app = create_app(testing=True)
    yield flask_app
    db_path = flask_app.config["DATABASE"]
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
