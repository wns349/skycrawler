# -*- coding: utf-8 -*-
import logging
import threading
import time
from multiprocessing import Event

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class Crawler(threading.Thread):
    def __init__(self, q, callback=None, driver_path="./driver/phantomjs.exe", driver_type="phantom",
                 page_wait_interval=5):
        super().__init__()
        self.q = q
        self.driver = None
        self.driver_path = driver_path
        self.driver_type = driver_type
        self.page_wait_interval = page_wait_interval
        self.callback = callback
        self.evt = Event()

    def run(self):
        while not self.evt.is_set():
            flight_info = self.q.get()
            try:
                if self.driver is None:
                    self.driver = start_driver(self.driver_path, self.driver_type)

                flight_info["url"] = {}
                flight_info["url"]["expedia"] = make_url_expedia(flight_info)
                flight_info["url"]["skyscanner"] = make_url_skyscanner(flight_info)

                goto_url(self.driver, flight_info["url"]["expedia"])

                time.sleep(self.page_wait_interval)
                logger.debug("Waiting until page loads.")

                flights = parse_expedia(self.driver, k=5)
                # flights = parse_skyscanner(driver, k=5)
                logger.debug("{}".format(flights))
                flight_info["flights"] = flights
            except Exception as e:
                flight_info["error"] = str(e)
                logger.error(str(e))

            finally:
                if self.driver is not None:
                    self.driver.quit()
                    self.driver = None
                flight_info["in_progress"] = False
                flight_info["updated_at"] = int(time.time() * 1000)
                if self.callback is not None:
                    self.callback(flight_info)

        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def stop(self):
        self.evt.set()


def get_flight_details(flight_info, callback=None, driver_path="./driver/phantomjs.exe", driver_type="phantom",
                       page_wait_interval=5):
    driver = None
    try:
        # create driver
        driver = start_driver(driver_path, driver_type)
        if driver is None:
            return

        flight_info["url"] = {}
        flight_info["url"]["expedia"] = make_url_expedia(flight_info)
        flight_info["url"]["skyscanner"] = make_url_skyscanner(flight_info)

        goto_url(driver, flight_info["url"]["expedia"])

        time.sleep(page_wait_interval)
        logger.debug("Waiting until page loads.")

        flights = parse_expedia(driver, k=5)
        # flights = parse_skyscanner(driver, k=5)
        logger.debug("{}".format(flights))
        flight_info["flights"] = flights

    except Exception as e:
        flight_info["error"] = str(e)
        logger.error(str(e))

    finally:
        if driver is not None:
            driver.quit()
        flight_info["in_progress"] = False
        flight_info["updated_at"] = int(time.time() * 1000)
        if callback is not None:
            callback(flight_info)


def start_driver(driver_path, driver_type):
    driver = None
    if driver_type == "phantom":
        driver = webdriver.PhantomJS(driver_path)
    elif driver_type == "chrome":
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
    return driver


def make_url_skyscanner(flight_info):
    url = "https://www.skyscanner.co.kr/transport/flights/"
    url += flight_info["origin"] + "/"
    url += flight_info["destination"] + "/"

    departing = flight_info["departing"].replace(".", "")[2:]
    returning = None
    if flight_info["returning"] != "":
        returning = flight_info["returning"].replace(".", "")[2:]
    url += departing + "/"
    url += returning + "/" if returning is not None else ""
    url += "?adults=1&children=0&adultsv2=1&childrenv2=&infants=0"
    url += "&canbinclass=economy&rtn=" + "1" if returning else "0"
    url += "&preferdirects=true"
    url += "&outboundaltsenabled=false&inboundaltsenabled=false&ref=home#results"

    return url


def make_url_expedia(flight_info):
    departure_date = flight_info["departing"]
    return_date = flight_info["returning"] if flight_info["returning"] != "" else None
    origin = flight_info["origin"]
    destination = flight_info["destination"]
    direct_only = flight_info["direct_only"]

    url = "https://www.expedia.co.kr/Flights-Search?flight-type=on&mode=search"
    url += "&starDate={}".format(departure_date)
    url += "&endDate={}".format(return_date)
    url += "&trip={}".format("roundtrip" if return_date is not None else "oneway")
    url += "&leg1=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(origin, destination, departure_date)
    url += "&leg2=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(destination, origin, return_date)
    url += "&passengers=children%3A{}%2Cadults%3A{}%2Cseniors%3A{}%2Cinfantinlap%3AY".format("0", "1", "0")
    url += "&options=cabinclass%3Aeconomy%2Cmaxhops%3A{}".format("0" if direct_only else "1")

    return url


def goto_url(driver, url):
    logger.info("Going to {}".format(url))
    driver.get(url)
    return url


def parse_skyscanner(driver, k=5):
    logger.debug(driver.page_source)
    flight_data = driver.find_element_by_class_name("day-list-container") \
        .find_element_by_tag_name("ul").find_elements_by_tag_name("li")
    infos = []

    idx = 0
    while len(infos) < k and idx < len(flight_data):
        try:
            data = flight_data[idx]
            info = {}

            tickets = data.find_elements_by_class_name("bpk-ticket__paper")
            tokens = tickets[0].text.split("\n")
            info["airline"] = tokens[0].replace(" ", "")
            info["depart"] = "{}-{}".format(tokens[1], tokens[5])
            if len(tokens) > 11:
                info["return"] = "{}-{}".format(tokens[7], tokens[11])
            tokens = tickets[1].text.split("\n")
            info["price"] = tokens[1]

            # info["airline"] = data.find_element_by_class_name("airline-name").text.replace(" ", "")
            #
            # leg_infos = data.find_elements_by_class_name("leg-info")
            # depart_leg_info = leg_infos[0]
            # spans = depart_leg_info.find_elements_by_tag_name("span")
            # spans = [s for s in spans if "LegInfo__times" in s.get_attribute("class")]
            # info["depart"] = "{}-{}".format(spans[0].text, spans[1].text)
            #
            # if len(leg_infos) > 1:
            #     return_leg_info = leg_infos[1]
            #     spans = return_leg_info.find_elements_by_tag_name("span")
            #     spans = [s for s in spans if "LegInfo__times" in s.get_attribute("class")]
            #     info["return"] = "{}-{}".format(spans[0].text, spans[1].text)
            #
            # div_price = data.find_element_by_class_name("bpk-ticket__paper")
            # div_price.find_element_by_tag_name("a").text

            infos.append(info)
            idx += 1
            pass
        except Exception as e:
            continue
    return infos


def parse_expedia(driver, k=5):
    flight_data = driver.find_element_by_id("flightModuleList").find_elements_by_tag_name("li")
    infos = []

    idx = 0
    while len(infos) < k and idx < len(flight_data):
        try:
            data = flight_data[idx]
            info = {}
            dt = data.find_element_by_xpath(".//span[@data-test-id='departure-time']").text
            at = data.find_element_by_xpath(".//span[@data-test-id='arrival-time']").text
            info["depart"] = "{}-{}".format(dt, at)
            info["return"] = ""
            info["airline"] = data.find_element_by_xpath(".//span[@data-test-id='airline-name']").text
            info["price"] = data.find_element_by_xpath(".//span[@data-test-id='listing-price-dollars']").text
            # info["price_type"] = data.find_element_by_xpath(".//span[@data-test-id='price-msg-route-type']").text
            # info["flight-info"] = data.find_element_by_xpath(".//span[@data-test-id='flight-info']").text
            infos.append(info)
            idx += 1
        except Exception as e:
            continue

    return infos
