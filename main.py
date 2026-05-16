import re
from collections import Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

MAX_TEXT_LENGTH = 50_000
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024


def analyze_text(text: str) -> dict:
    vowels_set = set("aeiou")
    num_vowels = 0
    num_consonants = 0
    letters_only = []

    for ch in text:
        lower_ch = ch.lower()
        if lower_ch.isalpha():
            letters_only.append(lower_ch)
            if lower_ch in vowels_set:
                num_vowels += 1
            else:
                num_consonants += 1

    chars_total = len(text)
    chars_no_spaces = len(re.sub(r"\s+", "", text))
    words = re.findall(r"\b[\w']+\b", text)
    word_count = len(words)
    sentence_count = len([s for s in re.split(r"[.!?]+", text) if s.strip()])
    avg_word_length = round(sum(len(w) for w in words) / word_count, 1) if word_count else 0

    most_common_letter = ""
    if letters_only:
        most_common_letter = Counter(letters_only).most_common(1)[0][0].upper()

    return {
        "vowels": num_vowels,
        "consonants": num_consonants,
        "characters": chars_total,
        "characters_no_spaces": chars_no_spaces,
        "words": word_count,
        "sentences": sentence_count,
        "avg_word_length": avg_word_length,
        "most_common_letter": most_common_letter or "—",
    }


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    return response


@app.errorhandler(413)
def payload_too_large(_e):
    return jsonify({"error": "Payload too large."}), 413


@app.errorhandler(400)
def bad_request(_e):
    return jsonify({"error": "Bad request."}), 400


@app.errorhandler(500)
def server_error(_e):
    return jsonify({"error": "Something went wrong."}), 500


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", max_length=MAX_TEXT_LENGTH)


@app.route("/analyze", methods=["POST"])
def analyze():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body."}), 400

    text = data.get("text", "")
    if not isinstance(text, str):
        return jsonify({"error": "Field 'text' must be a string."}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({
            "error": f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters."
        }), 400

    response = jsonify(analyze_text(text))
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
