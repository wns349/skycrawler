from flask_restplus import Namespace, Resource, fields, reqparse
from flask import request

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DT_INPUT_FORMAT = "%Y.%m.%d"
api = Namespace("flight", description="Flight")

flight_detail = api.model("Flight detail", {
    "depart_date": fields.String(),
    "return_date": fields.String(),
    "expedia": fields.String(),
    "skyscanner": fields.String()
})

flight_response = api.model("Flight response", {
    "origin": fields.String(required=True),
    "destination": fields.String(required=True),
    "details": fields.List(fields.Nested(flight_detail))
})


def _make_links(origin, destination, depart_date, return_date):
    response = {
        "depart_date": depart_date.strftime(DT_INPUT_FORMAT)
    }
    if return_date is not None:
        response["return_date"] = return_date.strftime(DT_INPUT_FORMAT)

    response["expedia"] = _make_link_expedia(origin, destination, depart_date, return_date)
    response["skyscanner"] = _make_link_skyscanner(origin, destination, depart_date, return_date)
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
    return_date = return_date.strftime(dt_format)
    url = "https://www.expedia.co.kr/Flights-Search?flight-type=on&mode=search"
    url += "&starDate={}".format(depart_date)
    url += "&endDate={}".format(return_date)
    url += "&trip={}".format("roundtrip" if return_date is not None else "oneway")
    url += "&leg1=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(origin, destination, depart_date)
    url += "&leg2=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(destination, origin, return_date)
    url += "&passengers=children%3A{}%2Cadults%3A{}%2Cseniors%3A{}%2Cinfantinlap%3AY".format("0", "1", "0")
    url += "&options=cabinclass%3Aeconomy%2Cmaxhops%3A{}".format("0" if direct_only else "1")
    return url


@api.route("/")
class Flight(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("origin", type=str, required=True, location="form", help="Airport code (e.g. ICN)")
    parser.add_argument("destination", type=str, required=True, location="form", help="Airport code (e.g. NRT)")
    parser.add_argument("base_date", type=str, required=True, location="form", help="Date format in yyyy.mm.dd")
    parser.add_argument("returning", type=int, required=True, location="form", help="x days")
    parser.add_argument("before", type=int, required=True, location="form", help="x days")
    parser.add_argument("after", type=int, required=True, location="form", help="x days")

    @api.expect(parser, validate=True)
    @api.marshal_with(flight_response)
    def post(self):
        # parse form
        data = request.form
        logger.info("RECV: {}".format(data))
        base_date = datetime.strptime(data["base_date"], DT_INPUT_FORMAT)
        is_round_trip = False
        if "returning" in data:
            return_after = int(data["returning"])
            is_round_trip = True
        before = int(data["before"]) if "before" in data else 0
        after = int(data["after"]) if "after" in data else 0

        # ready dates
        today = datetime.now()
        # today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        dates = []
        for i in range(-1 * before, after + 1):
            depart_date = base_date + timedelta(days=i)
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
            "details": []
        }
        for date in dates:
            response["details"].append(_make_links(data["origin"], data["destination"], date[0], date[1]))

        return response
