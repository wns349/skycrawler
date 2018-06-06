# -*- coding: utf-8 -*-
import time

from selenium import webdriver


def get_flight_details(flight_info, callback=None, driver_path="./driver/phantomjs.exe", driver_type="phantom"):
    driver = None
    try:
        # create driver
        driver = start_driver(driver_path, driver_type)
        if driver is None:
            return

        flight_info["url"] = goto_expedia(driver,
                                          flight_info["origin"],
                                          flight_info["destination"],
                                          flight_info["departing"],
                                          flight_info["returning"] if flight_info["returning"] != "" else None,
                                          flight_info["direct_only"])

        time.sleep(5)
        print("Waiting until page loads.")

        flights = parse_expedia(driver, k=5)
        print("{}".format(flights))
        flight_info["flights"] = flights

    except Exception as e:
        flight_info["error"] = str(e)
        print(str(e))

    finally:
        if driver is not None:
            driver.quit()
        flight_info["in_progress"] = False
        flight_info["updated"] = int(time.time() * 1000)
        if callback is not None:
            callback(flight_info)


def start_driver(driver_path, driver_type):
    driver = None
    if driver_type == "phantom":
        driver = webdriver.PhantomJS(driver_path)
    elif driver_type == "chrome":
        driver = webdriver.Chrome(driver_path)
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

    print("Going to {}".format(url))

    driver.get(url)

    return url


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

    return infos
