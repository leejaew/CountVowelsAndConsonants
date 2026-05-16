"""HTTP route handlers.

Views are intentionally *thin*. Their only jobs are:
  1. Parse and validate the incoming request.
  2. Delegate to the domain function (`analyzer.analyze`).
  3. Shape the HTTP response (status code, headers).

No business logic lives here. If a view grows past ~30 lines, that is
the signal to extract a helper into `analyzer.py` (or a new module).
"""

from flask import Blueprint, current_app, jsonify, render_template, request

from .analyzer import analyze

# A Blueprint, not direct app.route, because:
#   * It decouples route definitions from app construction (the
#     factory in __init__.py knows nothing about specific URLs).
#   * Adding a future `/api/v2` blueprint is symmetric — no
#     refactor of the existing registration code.
bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET"])
def index():
    """Render the single-page UI.

    The max-length limit is passed in from config so the template's
    `maxlength` attribute and JS counter stay in sync with the
    server's enforcement. Single source of truth = one place to
    change.
    """
    return render_template(
        "index.html",
        max_length=current_app.config["MAX_TEXT_LENGTH"],
    )


@bp.route("/analyze", methods=["POST"])
def analyze_route():
    """Validate the request, run the analyzer, return JSON.

    Validation is layered (defense in depth):
      * Flask's `MAX_CONTENT_LENGTH` rejects oversized HTTP bodies
        before they reach Python — cheapest possible filter.
      * `is_json` guards against wrong Content-Type.
      * `isinstance` checks defend against malformed JSON shapes
        (arrays, nulls, numbers in place of the expected object).
      * Length check enforces the application-level cap so a payload
        that fits in MAX_CONTENT_LENGTH but is still too long for
        analysis gets a clear, specific error.

    Each branch returns immediately — early-return style keeps the
    happy path uncluttered and unindented.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body."}), 400

    text = data.get("text", "")
    if not isinstance(text, str):
        return jsonify({"error": "Field 'text' must be a string."}), 400

    max_len = current_app.config["MAX_TEXT_LENGTH"]
    if len(text) > max_len:
        return (
            jsonify({"error": f"Text exceeds maximum length of {max_len} characters."}),
            400,
        )

    response = jsonify(analyze(text))
    # Per-route override of the default header policy: analysis
    # results are derived from user-submitted content and must never
    # be cached by intermediaries or the browser.
    response.headers["Cache-Control"] = "no-store"
    return response
