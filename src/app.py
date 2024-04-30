# app.py (Flask)
import getpass
import hashlib
import os
import socket
from uuid import uuid4

import tiktoken
from flask import Flask, render_template, request, session
from transformers import AutoModel, AutoTokenizer
from transformers.models.bert.configuration_bert import BertConfig


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
MODELS = {
    "cl100k_base": "gpt-4/gpt-3.5/text-embedding-ada-002/davinci-002",
    "p50k_base": "text-davinci-003/code-davinci-002/code-cushman-002",
    "gpt2": "gpt-2",
    "dnabert": "zhihan1996/DNABERT-2-117M",
}
TIKTOKEN_MODELS = ["cl100k_base", "p50k_base", "gpt2"]
HUGFACE_MODELS = ["dnabert"]
OPTIONS = {"text": "Text", "tokenids": "TokenIDs"}
DEFAULT_MODEL = "cl100k_base"
DEFAULT_OPTION = "text"

user_data = {}


@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        session["user_id"] = str(uuid4())

    if request.method == "POST":
        text = request.form["text"]
        model = request.form.get("model", DEFAULT_MODEL)
        option = request.form.get("option", DEFAULT_OPTION)
        print(f"model: {model}, option: {option}, text: {text[:100]}")
        highlighted_text, token_length = process_text(text, model, option)
        text_length = len(text)
        user_data[session["user_id"]] = {
            "highlighted_text": highlighted_text,
            "text_length": text_length,
            "token_length": token_length,
            "input_text": text,
            "model": model,
            "option": option,
        }
    else:
        user_data.pop(session["user_id"], None)

    input_text = user_data.get(session["user_id"], {}).get("input_text", "")
    highlighted_text = user_data.get(session["user_id"], {}).get("highlighted_text", "")
    text_length = user_data.get(session["user_id"], {}).get("text_length", 0)
    token_length = user_data.get(session["user_id"], {}).get("token_length", 0)
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
        token_length=token_length,
    )


def process_text(text, model, option):
    highlighted_text = ""
    color_index = 0
    if model in TIKTOKEN_MODELS:
        enc = tiktoken.get_encoding(model)
        token_ids = enc.encode(text)
        if option == "tokenids":
            return f"{token_ids}", len(token_ids)
        else:
            for token_id in token_ids:
                text = enc.decode([token_id])
                if text == "\n":
                    highlighted_text += text
                else:
                    color = COLORS[color_index]
                    highlighted_text += f'<span class="highlight-{color}">{text}</span>'
                    color_index = (color_index + 1) % len(COLORS)
            return highlighted_text, len(token_ids)
    elif model in HUGFACE_MODELS:
        _model = MODELS[model]
        if _model == "zhihan1996/DNABERT-2-117M":
            config = BertConfig.from_pretrained(_model)
        else:
            config = None
        tokenizer = AutoTokenizer.from_pretrained(_model, trust_remote_code=True)
        model = AutoModel.from_pretrained(_model, trust_remote_code=True, config=config)
        inputs = tokenizer(text.upper(), return_tensors="pt")
        if option == "tokenids":
            return f"{inputs['input_ids']}", len(inputs["input_ids"])
        else:
            for i, token_id in enumerate(inputs["input_ids"][0]):
                text = tokenizer.decode(token_id)
                if text == "\n":
                    highlighted_text += text
                else:
                    color = COLORS[color_index]
                    highlighted_text += f'<span class="highlight-{color}">{text}</span>'
                    color_index = (color_index + 1) % len(COLORS)
            return highlighted_text, len(inputs["input_ids"][0])
    else:
        return text, len(text)


if __name__ == "__main__":
    app.run(debug=True)
