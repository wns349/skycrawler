import logging
import os
from flask import Flask, render_template, request
from werkzeug.exceptions import BadRequest
from price_checker.apis import api

PORT = 5110

logger = logging.getLogger(__name__)


def _initialize_logger():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    logging.getLogger("selenium").setLevel(logging.FATAL)
    logging.getLogger("werkzeug").setLevel(logging.FATAL)
    logging.getLogger("engineio").setLevel(logging.FATAL)


def _initialize_app():
    app = Flask(__name__)
    app.secret_key = "simple_url_gen"
    app.processes = 1
    app.static_folder = os.path.join(os.path.dirname(__file__), "static")
    app.template_folder = os.path.join(os.path.dirname(__file__), "templates")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return 'bad request!', 400

    api.init_app(app)

    return app


def _main():
    _initialize_logger()

    app = _initialize_app()
    app.run("127.0.0.1", port=PORT, debug=True)


if __name__ == "__main__":
    _main()
