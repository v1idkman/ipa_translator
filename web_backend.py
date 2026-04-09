import os
import subprocess
import sys

from flask import Flask, jsonify, request, send_from_directory

import english_to_ipa_model as model


REQUIRED_PACKAGES = {
    "Flask": "flask",
}

for package, module_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


app = Flask(__name__, static_folder="web")
lexicon = model.load_northwest_american_lexicon()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    prompt_text = (payload.get("prompt_text") or "").strip()
    recognized_text = (payload.get("recognized_text") or "").strip()

    if not prompt_text:
        return jsonify({"error": "prompt_text is required"}), 400

    result = model.analyze_prompt_vs_recognized(
        prompt_text=prompt_text,
        recognized_text=recognized_text,
        lexicon=lexicon,
    )

    return jsonify(result)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=False)
