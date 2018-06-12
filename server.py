import configparser
import json
import logging
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing import Queue

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import crawler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("selenium").setLevel(logging.FATAL)
logging.getLogger("werkzeug").setLevel(logging.FATAL)
logging.getLogger("engineio").setLevel(logging.FATAL)

config_master = configparser.ConfigParser()
config_master.read("./config.ini")
config = config_master["DEFAULT"]

app = Flask(__name__)
app.secret_key = "helloworld1234"
app.processes = 1
socketio = SocketIO(app)


def save_file():
    with open("data.json", "w", encoding="utf-8") as outfile:
        json.dump(flight_qs, outfile, ensure_ascii=False)


def load_file():
    try:
        with open("data.json", "r", encoding="utf-8") as outfile:
            return json.load(outfile, encoding="utf-8")
    except Exception as e:
        logger.error(e)
        return None


flight_qs = load_file()
if flight_qs is None:
    flight_qs = {}

logger.info("flightQs: {}".format(flight_qs))


@app.route("/")
def index():
    return render_template("index.html", async=socketio.async_mode)


@socketio.on("connect", namespace="/flights")
def connect():
    emit("response", {"data": flight_qs})
    logger.info("Client connected")


@socketio.on("disconnect", namespace="/flights")
def disconnect():
    logger.info("Client disconnected.")


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
    logger.info("{} added.".format(message["id"]))

    emit("flight-info", {"data": flight_info}, broadcast=True)
    save_file()


@socketio.on("delete", namespace="/flights")
def delete(message):
    if message["id"] in flight_qs:
        # flight_qs.pop(message["id"], None)
        flight_qs[message["id"]]["deleted"] = True
        logger.info("{} deleted.".format(message["id"]))
        save_file()


@socketio.on("refresh", namespace="/flights")
def refresh(message):
    if message["id"] in flight_qs:
        if flight_qs[message["id"]]["in_progress"] is False:
            flight_qs[message["id"]]["updated_at"] -= (int(config["refresh_interval"]) + 5)
            logger.info("{} refresh requested".format(message["id"]))


def emit_flight_info(flight_info):
    flight_qs[flight_info["id"]] = flight_info
    socketio.emit("flight-info", {"data": flight_info}, broadcast=True, namespace="/flights")
    save_file()


def dispatcher():
    with ThreadPoolExecutor(max_workers=5) as executor:
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
                        and f["updated_at"] + int(config["refresh_interval"]) <= int(time.time() * 1000):
                    f["in_progress"] = True
                    executor.submit(crawler.get_flight_details,
                                    f,
                                    emit_flight_info,
                                    config["driver_path"],
                                    config["driver_type"]),
                    int(config["page_wait_interval"])
                    cnt += 1

            deleted = [f["id"] for f in flight_qs.values() if f["deleted"]]
            for d in deleted:
                flight_qs.pop(d, None)

            if cnt == 0:
                time.sleep(1)


def dispatcher_q():
    _crawler = None
    try:
        q = Queue()
        _crawler = crawler.Crawler(q, callback=emit_flight_info,
                                   driver_path=config["driver_path"],
                                   driver_type=config["driver_type"],
                                   page_wait_interval=int(config["page_wait_interval"]))
        _crawler.daemon = True
        _crawler.start()
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
                        and f["updated_at"] + int(config["refresh_interval"]) <= int(time.time() * 1000):
                    f["in_progress"] = True
                    q.put(f)
                    cnt += 1

            deleted = [f["id"] for f in flight_qs.values() if f["deleted"]]
            for d in deleted:
                flight_qs.pop(d, None)

            if cnt == 0:
                time.sleep(1)
    finally:
        _crawler.stop()


if __name__ == "__main__":
    t = threading.Thread(target=dispatcher)
    t.setDaemon(True)
    t.start()
    socketio.run(app)
    t.join()
    logger.info("Bye")
