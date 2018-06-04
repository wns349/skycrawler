# -*- coding: utf-8 -*-
import platform
from datetime import datetime

from selenium import webdriver


def start_driver():
    if platform.system() == "Darwin":
        driver = webdriver.Chrome("./driver/chromedriver")
    else:
        #driver = webdriver.Chrome("./driver/chromedriver.exe")
        driver = webdriver.PhantomJS("./driver/phantomjs.exe")
    return driver


def goto_expedia(driver,
                 origin,
                 destination,
                 departure_date,
                 return_date=None,
                 direct_only=True):
    url = "https://www.expedia.co.kr/Flights-Search?flight-type=on&mode=search"
    url += "&starDate={}".format(departure_date)
    url += "&endDate={}".format(return_date)
    url += "&trip={}".format("roundtrip" if return_date is not None else "oneway")
    url += "&leg1=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(origin, destination, departure_date)
    url += "&leg2=from%3A{}%2Cto%3A{}%2Cdeparture%3A{}TANYT".format(destination, origin, return_date)
    url += "&passengers=children%3A{}%2Cadults%3A{}%2Cseniors%3A{}%2Cinfantinlap%3AY".format("0", "1", "0")
    url += "&options=cabinclass%3Aeconomy%2Cmaxhops%3A{}".format("0" if direct_only else "1")

    driver.get(url)


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
            info["time"] = "{}-{}".format(dt, at)
            info["airline"] = data.find_element_by_xpath(".//span[@data-test-id='airline-name']").text
            info["price"] = data.find_element_by_xpath(".//span[@data-test-id='listing-price-dollars']").text
            # info["price_type"] = data.find_element_by_xpath(".//span[@data-test-id='price-msg-route-type']").text
            # info["flight-info"] = data.find_element_by_xpath(".//span[@data-test-id='flight-info']").text
            infos.append(info)
            idx += 1
        except:
            continue

    return datetime.now(), infos

