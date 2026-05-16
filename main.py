import re
from collections import Counter
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


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
    chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    words = re.findall(r"\b[\w']+\b", text)
    word_count = len(words)
    sentence_count = len([s for s in re.split(r"[.!?]+", text) if s.strip()])
    line_count = len([line for line in text.splitlines() if line.strip()]) if text.strip() else 0
    avg_word_length = round(sum(len(w) for w in words) / word_count, 1) if word_count else 0
    reading_time_min = max(1, round(word_count / 200)) if word_count else 0

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
        "lines": line_count,
        "avg_word_length": avg_word_length,
        "reading_time_min": reading_time_min,
        "most_common_letter": most_common_letter or "—",
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    return jsonify(analyze_text(text))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
