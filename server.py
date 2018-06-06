import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import crawler

# DRIVER_PATH = "./driver/phantomjs"
# DRIVER_TYPE = "phantom"
DRIVER_PATH = "./driver/chromedriver"
DRIVER_TYPE = "chrome"
REFRESH_INTERVAL = (5 * 60 * 1000)

flight_qs = {}

app = Flask(__name__)
app.secret_key = "helloworld1234"
socketio = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html", async=socketio.async_mode)


@socketio.on("connect", namespace="/flights")
def connect():
    emit("response", {"data": flight_qs})
    print("Client connected")


@socketio.on("disconnect", namespace="/flights")
def disconnect():
    print("Client disconnected.")


@socketio.on("request", namespace="/flights")
def request(message):
    flight_info = {}
    flight_info["id"] = message["id"]
    flight_info["origin"] = message["origin"]
    flight_info["destination"] = message["destination"]
    flight_info["departing"] = message["departing"]
    flight_info["returning"] = message["returning"]
    flight_info["direct_only"] = False
    flight_info["updated_at"] = int(time.time() * 1000) - (60 * 60 * 1000);
    flight_info["flights"] = []
    flight_info["in_progress"] = False
    flight_info["error"] = None
    flight_info["deleted"] = False
    flight_qs[flight_info["id"]] = flight_info
    print("{} added.".format(message["id"]))

    emit("flight-info", {"data": flight_info}, broadcast=True)


@socketio.on("delete", namespace="/flights")
def delete(message):
    if message["id"] in flight_qs:
        # flight_qs.pop(message["id"], None)
        flight_qs[message["id"]]["deleted"] = True
        print("{} deleted.".format(message["id"]))


@socketio.on("refresh", namespace="/flights")
def refresh(message):
    if message["id"] in flight_qs:
        if flight_qs[message["id"]]["in_progress"] is False:
            flight_qs[message["id"]]["updated_at"] -= (REFRESH_INTERVAL + 5)
            print("{} refresh requested".format(message["id"]))


def emit_flight_info(flight_info):
    socketio.emit("flight-info", {"data": flight_info}, broadcast=True, namespace="/flights")


def dispatcher():
    executor = None
    try:
        executor = ThreadPoolExecutor(max_workers=10)
        while True:
            if len(flight_qs) == 0:
                time.sleep(1)
                continue

            cnt = 0
            ids = [x for x in flight_qs.keys()]
            for i in ids:
                f = flight_qs[i]
                if f["in_progress"] is False \
                        and f["deleted"] is False \
                        and f["updated_at"] + REFRESH_INTERVAL <= int(time.time() * 1000):
                    f["in_progress"] = True
                    executor.submit(crawler.get_flight_details(f, callback=emit_flight_info,
                                                               driver_path=DRIVER_PATH,
                                                               driver_type=DRIVER_TYPE))
                    cnt += 1

            deleted = [f["id"] for f in flight_qs.values() if f["deleted"]]
            for d in deleted:
                flight_qs.pop(d, None)

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
