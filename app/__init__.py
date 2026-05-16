"""Application package.

Exposes the `create_app` factory. Importing this module has no side
effects: nothing binds to a port, no global Flask object is created.
That is intentional — it lets tests build isolated app instances and
keeps production startup explicit (`main.py` calls the factory).
"""

from flask import Flask

from .config import Config
from .security import register_security
from .views import bp


def create_app(config_class: type = Config) -> Flask:
    """Build and return a fully-configured Flask application.

    Why the application-factory pattern (instead of a module-level
    `app = Flask(__name__)`):
      * Tests can construct an app with a TestConfig without monkey-
        patching globals.
      * Future deployments (e.g. staging vs. prod) swap configs by
        passing a different class — no environment branching here.
      * Avoids import-time side effects, which makes the import graph
        predictable.

    `template_folder` / `static_folder` are made explicit because the
    `app/` package is nested one level below the project root where
    `templates/` and `static/` actually live.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    # Cross-cutting concerns (headers, error handlers) registered once,
    # centrally, so individual routes never have to think about them.
    register_security(app)

    # Routes live in a Blueprint rather than directly on `app`. Even
    # with a single group today, this gives us a zero-cost extension
    # point: a future `api/v2` blueprint plugs in without touching
    # this factory.
    app.register_blueprint(bp)

    return app
