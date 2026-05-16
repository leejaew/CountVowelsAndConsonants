"""Application configuration.

A class — not a flat module of constants — because Flask's
`app.config.from_object()` reads attributes off a class, and because
subclassing (`class TestConfig(Config): MAX_TEXT_LENGTH = 100`) is the
cleanest way to override a single value without duplicating the rest.
"""


class Config:
    """Base configuration shared across environments.

    Values here are deliberately conservative. They are the *only*
    knobs the rest of the codebase reads for limits, so changing a
    limit is a one-line edit confined to this file.
    """

    # Maximum number of characters we are willing to analyze. Bounds
    # the worst-case CPU/memory of `analyze()` and is enforced
    # explicitly in the view layer so the user gets a clear error.
    MAX_TEXT_LENGTH: int = 50_000

    # Hard ceiling on raw HTTP request body size. Enforced by Flask
    # itself before any Python code runs — first line of defense
    # against memory-exhaustion payloads. ~2.5x MAX_TEXT_LENGTH to
    # leave headroom for JSON envelope and unicode expansion.
    MAX_CONTENT_LENGTH: int = 128 * 1024
