from flask_restplus import Namespace, Resource, fields, reqparse
from flask import request
from werkzeug.exceptions import InternalServerError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DT_INPUT_FORMAT = "%Y.%m.%d"
DT_OUTPUT_FORMAT = "%Y.%m.%d(%a)"
api = Namespace("flight", description="Flight")

parser = reqparse.RequestParser()
parser.add_argument("origin", type=str, required=True, location="form", help="Airport code (e.g. ICN)")
parser.add_argument("destination", type=str, required=True, location="form", help="Airport code (e.g. NRT)")
parser.add_argument("start_date", type=str, required=True, location="form", help="Date format in yyyy.mm.dd")
parser.add_argument("end_date", type=str, required=True, location="form", help="Date format in yyyy.mm.dd")
parser.add_argument("duration", type=int, required=True, location="form")
parser.add_argument("duration_text", type=str, required=False, location="form")

flight_detail = api.model("Flight detail", {
    "depart_date": fields.String(),
    "return_date": fields.String(),
    "expedia": fields.String(),
    "skyscanner": fields.String(),
    "interpark_domestic": fields.String()
})

flight_response = api.model("Flight response", {
    "origin": fields.String(required=True),
    "destination": fields.String(required=True),
    "duration": fields.String(),
    "details": fields.List(fields.Nested(flight_detail))
})


def _make_links(origin, destination, depart_date, return_date):
    response = {
        "depart_date": depart_date.strftime(DT_OUTPUT_FORMAT)
    }
    if return_date is not None:
        response["return_date"] = return_date.strftime(DT_OUTPUT_FORMAT)
    else:
        response["return_date"] = "N/A"

    response["expedia"] = _make_link_expedia(origin, destination, depart_date, return_date)
    response["skyscanner"] = _make_link_skyscanner(origin, destination, depart_date, return_date)
    response["interpark_domestic"] = _make_link_interpark_domestic(origin, destination, depart_date, return_date)
    return response


def _make_link_skyscanner(origin, destination, depart_date, return_date, direct_only=True):
    dt_format = "%Y%m%d"
    url = "https://www.skyscanner.co.kr/transport/flights/"
    url += origin + "/"
    url += destination + "/"
    url += depart_date.strftime(dt_format) + "/"
    url += return_date.strftime(dt_format) + "/" if return_date is not None else ""
    url += "?adults=1&children=0&adultsv2=1&childrenv2=&infants=0"
    url += "&canbinclass=economy&rtn=" + "1" if return_date is not None else "0"
    url += "&preferdirects=true"
    url += "&outboundaltsenabled=false&inboundaltsenabled=false&ref=home#results"
    return url


def _make_link_expedia(origin, destination, depart_date, return_date, direct_only=True):
    dt_format = "%Y.%m.%d"
    depart_date = depart_date.strftime(dt_format)
    if return_date is not None:
        return_date = return_date.strftime(dt_format)
    url = "https://www.expedia.co.kr/Flights-Search?flight-type=on&mode=search"
    url += "&starDate={}".format(depart_date)
    if return_date is not None:
        url += "&endDate={}".format(return_date)
    url += "&trip={}".format("roundtrip" if return_date is not None else "oneway")
    url += "&leg1=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(origin, destination, depart_date)
    url += "&leg2=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(destination, origin, return_date)
    url += "&passengers=children%3A{}%2Cadults%3A{}%2Cseniors%3A{}%2Cinfantinlap%3AY".format("0", "1", "0")
    url += "&options=cabinclass%3Aeconomy%2Cmaxhops%3A{}".format("0" if direct_only else "1")
    return url


def _make_link_interpark_domestic(origin, destination, depart_date, return_date, direct_only=True):
    dt_format = "%Y%m%d"
    depart_date = depart_date.strftime(dt_format)
    if return_date is not None:
        return_date = return_date.strftime(dt_format)
    url = "http://domair.interpark.com/dom/main.do?adt=1&chd=0&inf=0"
    url += "&depdate={}".format(depart_date)
    if return_date is not None:
        url += "&retdate={}".format(return_date)
        url += "&trip=RT"
    url += "&dep={}&arr={}".format(origin, destination)
    url += "&dep2={}&arr2={}".format(destination, origin)
    return url


@api.errorhandler(ValueError)
def handler_value_error(error):
    return str(error), 500


@api.route("/")
class Flight(Resource):
    @api.expect(parser, validate=True)
    @api.marshal_with(flight_response)
    def post(self):
        # parse form
        data = request.form
        logger.info("RECV: {}".format(data))
        start_date = datetime.strptime(data["start_date"], DT_INPUT_FORMAT)
        end_date = datetime.strptime(data["end_date"], DT_INPUT_FORMAT)
        is_round_trip = False
        return_after = 0
        if "duration" in data and data["duration"] != "":
            return_after = int(data["duration"])
            if return_after < 0:
                is_round_trip = False
            else:
                is_round_trip = True

        # ready dates
        today = datetime.now()
        total_days = (end_date - start_date).days + 1
        dates = []
        for i in range(total_days):
            depart_date = start_date + timedelta(days=i)
            if depart_date < today:
                continue
            if is_round_trip:
                return_date = depart_date + timedelta(days=return_after)
            else:
                return_date = None
            dates.append((depart_date, return_date))
        logging.info("{} dates ready to process.".format(len(dates)))

        # make response
        response = {
            "origin": data["origin"],
            "destination": data["destination"],
            "details": [],
            "duration": data["duration_text"]
        }
        for date in dates:
            response["details"].append(_make_links(data["origin"], data["destination"], date[0], date[1]))

        return response
