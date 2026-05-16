# Text Analyzer

A small Flask web app that analyzes text and returns live statistics: vowel and consonant counts (the original feature), plus word count, character counts, sentence count, average word length, and most-common letter.

## Stack

- Python 3.11
- Flask (web framework)
- Gunicorn (production WSGI server)
- Vanilla HTML / CSS / JS frontend (no build step)

## Project structure

```
main.py                  # WSGI entry point (gunicorn loads `main:app`)
app/
  __init__.py            # Application factory
  config.py              # Centralized configuration
  analyzer.py            # Pure text-analysis logic (Flask-free)
  security.py            # Security headers + JSON error handlers
  views.py               # HTTP route handlers (Blueprint)
templates/index.html     # Single-page UI
static/
  app.js                 # Frontend logic (debounced fetch to /analyze)
  styles.css             # Styles
requirements.txt
```

## Architecture notes

- **Application factory**: `create_app()` builds and returns the Flask app; no import-time side effects.
- **Pure-function analyzer**: `app/analyzer.py` has no Flask dependency, can be reused or tested in isolation.
- **Performance**: regexes are pre-compiled at import time; `analyze()` is memoized with a bounded LRU cache.
- **Layered validation** on `/analyze`: HTTP body size (Flask), Content-Type, JSON shape, text type, application-level length.
- **Security baseline** (applied via `after_request` hook): strict CSP without `unsafe-inline`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`. `Cache-Control: no-store` on analyzer responses.

## Running locally

```bash
pip install -r requirements.txt
python3 main.py
# → http://localhost:5000
```

## Production

```bash
gunicorn --bind=0.0.0.0:8080 main:app
```

## API

`POST /analyze`

Request:
```json
{ "text": "Hello world!" }
```

Response (`200 application/json`):
```json
{
  "vowels": 3,
  "consonants": 7,
  "characters": 12,
  "characters_no_spaces": 11,
  "words": 2,
  "sentences": 1,
  "avg_word_length": 5.0,
  "most_common_letter": "L"
}
```

Error responses use the same JSON shape: `{"error": "..."}` with status `400`, `413`, `415`, or `500`.
