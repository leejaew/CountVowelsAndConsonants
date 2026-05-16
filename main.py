"""WSGI entry point.

Kept deliberately tiny. Production runs `gunicorn main:app`, so all
that needs to live at module top level is the `app` symbol. Anything
beyond that — config, routes, security — belongs in the `app/`
package, behind the factory.
"""

from app import create_app

# Module-level `app` exists solely so WSGI servers can import it as
# `main:app`. The factory keeps this import side-effect minimal: no
# routes are evaluated and no listeners bind until the WSGI server
# actually serves a request.
app = create_app()


if __name__ == "__main__":
    # Local dev only. Production uses gunicorn (see `.replit`).
    app.run(host="0.0.0.0", port=5000)
