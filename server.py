import os
import threading
from flask import Flask, send_file, send_from_directory, jsonify
from yml_generator import generate_yml

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "SkyLots Bot Server працює!"})


@app.route("/feed.yml")
def feed():
    yml_file = "feed.yml"
    if not os.path.exists(yml_file):
        generate_yml()
    return send_file(yml_file, mimetype="application/xml")


@app.route("/photos/<filename>")
def photo(filename):
    return send_from_directory("photos", filename)


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_flask()
