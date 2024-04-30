# app.py (Flask)
import getpass
import hashlib
import os
import socket
from uuid import uuid4

from flask import Flask, render_template, request, session


def generate_default_secret_key():
    username = getpass.getuser()
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # Concatenate username, IP address, and hostname
    concatenated_info = f"{username}-{ip_address}-{hostname}"
    # Hash the concatenated string using SHA-256
    hashed_info = hashlib.sha256(concatenated_info.encode()).hexdigest()
    return hashed_info


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", generate_default_secret_key())

COLORS = ["red", "green", "blue", "purple", "orange"]
MODELS = {"vowels": "Highlight vowels", "consonants": "Highlight consonants", "numbers": "Highlight numbers"}
OPTIONS = {"text": "Text", "tokenids": "TokenIDs"}
DEFAULT_MODEL = "vowels"
DEFAULT_OPTION = "text"

user_data = {}


@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        session["user_id"] = str(uuid4())

    if request.method == "POST":
        print(request.form)
        text = request.form["text"]
        model = request.form.get("model", DEFAULT_MODEL)
        option = request.form.get("option", DEFAULT_OPTION)
        highlighted_text = process_text(text, model, option)
        text_length = len(text)
        user_data[session["user_id"]] = {
            "highlighted_text": highlighted_text,
            "text_length": text_length,
            "input_text": text,
            "model": model,
            "option": option,
        }
    else:
        user_data.pop(session["user_id"], None)

    input_text = user_data.get(session["user_id"], {}).get("input_text", "")
    highlighted_text = user_data.get(session["user_id"], {}).get("highlighted_text", "")
    text_length = user_data.get(session["user_id"], {}).get("text_length", 0)
    model = user_data.get(session["user_id"], {}).get("model", DEFAULT_MODEL)
    option = user_data.get(session["user_id"], {}).get("option", DEFAULT_OPTION)

    return render_template(
        "index.html",
        models=MODELS,
        default_model=model,
        options=OPTIONS,
        default_option=option,
        input_text=input_text,
        highlighted_text=highlighted_text,
        text_length=text_length,
    )


def process_text(text, model, option):
    highlighted_text = ""
    color_index = 0
    for i, char in enumerate(text):
        if char == " " or char == "\n":
            highlighted_text += char
        else:
            if model == "vowels":
                if char.lower() in "aeiou":
                    color = COLORS[color_index]
                    highlighted_text += f'<span class="highlight-{color}">{char}</span>'
                    color_index = (color_index + 1) % len(COLORS)
                else:
                    highlighted_text += char
            elif model == "consonants":
                if char.lower() not in "aeiou":
                    color = COLORS[color_index]
                    highlighted_text += f'<span class="highlight-{color}">{char}</span>'
                    color_index = (color_index + 1) % len(COLORS)
                else:
                    highlighted_text += char
            elif model == "numbers":
                if char.isdigit():
                    color = COLORS[color_index]
                    highlighted_text += f'<span class="highlight-{color}">{char}</span>'
                    color_index = (color_index + 1) % len(COLORS)
                else:
                    highlighted_text += char
    return option + highlighted_text


if __name__ == "__main__":
    app.run(debug=True)
