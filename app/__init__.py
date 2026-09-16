import os
import tempfile

from flask import Flask

from app import db as db_module


def create_app(testing=False, database=None):
    """Application factory.

    Pass ``testing=True`` to run against an isolated, throwaway SQLite
    database (a temp file) instead of the app's regular instance database.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-secret-key"),
        DATABASE=database or os.path.join(app.instance_path, "polls.sqlite"),
        TESTING=testing,
    )

    if testing:
        # Use a fresh temp file per test app so tests never touch the
        # real instance database and don't share state with each other.
        if database is None:
            fd, path = tempfile.mkstemp(suffix=".sqlite")
            os.close(fd)
            app.config["DATABASE"] = path
        app.config["TEST_DB_FD_PATH"] = app.config["DATABASE"]
    else:
        os.makedirs(app.instance_path, exist_ok=True)

    db_module.init_app(app)

    from app import routes

    app.register_blueprint(routes.bp)

    with app.app_context():
        db_module.init_db()

    return app
