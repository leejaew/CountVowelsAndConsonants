from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    input_string = ""
    if request.method == "POST":
        input_string = request.form.get("text", "")
        num_vowels = 0
        num_consonants = 0
        for ch in input_string:
            ch = ch.lower()
            if ch in "aeiou":
                num_vowels += 1
            elif ch.isalpha():
                num_consonants += 1
        result = {"vowels": num_vowels, "consonants": num_consonants}
    return render_template("index.html", result=result, input_string=input_string)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
