import datetime
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import crawler

flight_qs = {}

app = Flask(__name__)
app.secret_key = "helloworld1234"
socketio = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect", namespace="/flights")
def connect():
    emit("response", {"data": flight_qs})


@socketio.on("disconnect", namespace="/flights")
def disconnect():
    print("Disconnected.")


@socketio.on("request", namespace="/flights")
def request(message):
    flight_info = {}
    flight_info["id"] = message["id"]
    flight_info["origin"] = message["origin"]
    flight_info["destination"] = message["destination"]
    flight_info["departing"] = message["departing"]
    flight_info["returning"] = message["returning"] if message["returning"] != "" else None
    flight_info["direct_only"] = False
    flight_info["updated_at"] = datetime.datetime.now() - datetime.timedelta(hours=1)
    flight_info["flights"] = []
    flight_info["in_progress"] = False
    flight_info["error"] = None
    flight_qs[flight_info["id"]] = flight_info


def emit_flight_info(flight_info):
    with app.test_request_context():
        socketio.emit("flight-info", {"data": flight_info}, broadcast=True)


def dispatcher():
    executor = None
    try:
        executor = ThreadPoolExecutor(max_workers=10)
        while True:
            if len(flight_qs) == 0:
                time.sleep(1)
                continue

            cnt = 0
            for f in flight_qs:
                if f["in_progress"] is False and f["updated_at"] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
                    f["in_progress"] = True
                    executor.submit(crawler.get_flight_details(f, callback=emit_flight_info))
                    cnt += 1

            if cnt == 0:
                time.sleep(1)
    finally:
        executor.shutdown()


if __name__ == "__main__":
    t = threading.Thread(target=dispatcher)
    t.setDaemon(True)
    t.start()
    socketio.run(app)
    t.join()
    print("Bye")
