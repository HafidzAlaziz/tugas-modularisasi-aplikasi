"""Perpustakaan Kampus — Versi MODULAR.

app.py hanya bertugas merakit modul: konfigurasi, repositori, template filter, dan blueprint.
"""
from flask import Flask

import config
from repositori import RepositoriJson
from rute import api, web
from utils.format import format_rupiah


def create_app(repo=None) -> Flask:
    app = Flask(__name__)
    app.config["REPO"] = repo or RepositoriJson(config.DATA_FILE)
    app.jinja_env.filters["rupiah"] = format_rupiah

    app.register_blueprint(web)
    app.register_blueprint(api, url_prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
