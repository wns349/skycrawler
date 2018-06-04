from flask import (
    Blueprint, render_template, request, flash
)
from server import flight_infos

bp = Blueprint("controller", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        add_flight(request)
    return render_template("index.html")


@bp.route("/flight_info", methods=["GET"])
def get_flight_info():
    return render_template("flight_info.html", flight_infos=flight_infos.values())


@bp.route("/flight_info/<id>", methods=["DELETE"])
def delete_flight_info(id):
    flight_infos.pop(id, None)
    return render_template("flight_info.html", flight_infos=flight_infos.values())


def add_flight(r):
    flash("{} {} {} {}".format(r.form["origin"],
                               r.form["destination"],
                               r.form["departing"],
                               r.form["returning"])
          )
