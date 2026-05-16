"""Cross-cutting security concerns.

All HTTP response headers and JSON error handlers live here so the
security policy has *one* canonical home. A future audit, CSP tweak,
or new error code is a single-file change — routes never need editing.

Implemented as functions wired via `register_security(app)` rather
than as a Flask extension class, because a class would add ceremony
without giving us anything (no per-request state, no configuration
surface beyond the headers themselves).
"""

from flask import Flask, jsonify

# CSP is composed from a dict of named directives instead of one long
# string. Two reasons:
#   1. Adding/removing a source (e.g. allowing a CDN) is a one-line
#      dict edit, not a string-surgery exercise.
#   2. The directive names become greppable — a developer searching
#      for "script-src" lands here immediately.
_CSP_DIRECTIVES: dict[str, str] = {
    "default-src": "'self'",
    "style-src": "'self'",
    "script-src": "'self'",
    "img-src": "'self' data:",
    "connect-src": "'self'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'none'",
}

# Header dict is module-level (built once at import) rather than
# rebuilt per-request. Each value is a plain string so Flask can copy
# it into response headers with no further work.
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": "; ".join(
        f"{name} {value}" for name, value in _CSP_DIRECTIVES.items()
    ),
}


def register_security(app: Flask) -> None:
    """Attach security headers and JSON error handlers to `app`.

    The `after_request` hook runs for *every* response — HTML, JSON,
    static files, errors — which is exactly what defense-in-depth
    headers want. Headers are assigned unconditionally (not via
    `setdefault`) so a baseline security policy is guaranteed even if
    upstream code accidentally set a weaker value. Per-route headers
    that are *not* in `_SECURITY_HEADERS` (e.g. `Cache-Control`) are
    untouched.

    Error handlers return JSON, not HTML, because every endpoint that
    matters to a client today is a JSON API. An HTML 500 page would
    be a content-type lie that breaks the frontend's `res.json()`.
    """

    @app.after_request
    def _apply_headers(response):
        for name, value in _SECURITY_HEADERS.items():
            response.headers[name] = value
        return response

    # One handler per status we expect to surface. Keeping them
    # explicit (rather than a single catch-all) makes it obvious at a
    # glance which failure modes the app contractually handles.
    @app.errorhandler(400)
    def _bad_request(_e):
        return jsonify({"error": "Bad request."}), 400

    @app.errorhandler(413)
    def _payload_too_large(_e):
        return jsonify({"error": "Payload too large."}), 413

    @app.errorhandler(415)
    def _unsupported_media(_e):
        return jsonify({"error": "Unsupported media type."}), 415

    @app.errorhandler(500)
    def _server_error(_e):
        # Generic message on purpose: never leak stack traces or
        # internal details to a client.
        return jsonify({"error": "Something went wrong."}), 500
