#!/usr/bin/env python

# requires: netifaces for looking up IP in readable way
# requires: requests human readable HTTP requests

# 要クラス化&selfで引き回し

import json
import socket
import time
import urllib
from sys import exit

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

import scrollphat


class MainApp:

    lotate_time_sec = 0.1      # スクロールの更新間隔(sec)
    update_time_sec = 60 * 60  # 予報の更新間隔(sec)

    item = ""
    output = ""
    weather = ""
    location = ""
    location_string = ""

    def get_location(self):
        res = requests.get('http://ipinfo.io')
        if res.status_code == 200:
            json_data = json.loads(res.text)
            return json_data
        return {}

    def get_location_now(self):
        self.location = self.get_location()
        self.location_string = self.location["city"] + ", " + self.location["country"]

    # Python 2 vs 3 breaking changes.
    def encode(self, qs):
        val = ""
        try:
            val = urllib.urlencode(qs).replace("+", "%20")
        except:
            val = urllib.parse.urlencode(qs).replace("+", "%20")
        return val

    def get_weather(self, address):
        base = "https://query.yahooapis.com/v1/public/yql?"
        query = "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text=\"" + address + "\")"
        qs = {"q": query, "format": "json", "env": "store://datatables.org/alltableswithkeys"}

        uri = base + self.encode(qs)

        res = requests.get(uri)
        if res.status_code == 200:
            json_data = json.loads(res.text)
            return json_data
        return {}

    def get_weather_days(self, days):
        self.weather = self.get_weather(self.location_string)
        self.output = ""

        # Feel free to pick out other data here, for the scrolling message
        for x in range(0, days):
            self.item = self.weather["query"]["results"]["channel"]["item"]["forecast"][x]
            self.output = self.output + " " + self.item["day"] + ": " + self.item["text"] + " - L: " + self.item["low"] + "F - H: " + self.item["high"] + "F"

    def get_weather_info(self):
        print("")
        print(" --- Weather Info ---")
        print("       Get: " + self.weather["query"]["created"][:-1])
        print("  Location: " + self.location_string)
        print("      Data: " + self.output)
        print(" --------------------")

    def scroll_message(self):

        time_count_par_sec = 1 / self.lotate_time_sec
        time_count_limit = time_count_par_sec * self.update_time_sec
        time_count = time_count_limit
        while True:
            try:
                if time_count >= time_count_limit:
                    print("Update...")
                    self.get_weather_days(7)
                    self.get_weather_info()
                    scrollphat.write_string(self.output)
                    scrollphat.update()
                    time_count = 0

                scrollphat.scroll()
                scrollphat.update()
                time.sleep(self.lotate_time_sec)
                time_count += 1

            except KeyboardInterrupt:
                print("\nInterrupted Ctrl + C !!\n")
                return


if __name__ == '__main__':
    ma = MainApp()

    scrollphat.set_brightness(4)

    ma.get_location_now()

    if ma.location["city"] != None:
        ma.weather = ma.get_weather(ma.location_string)

        ma.scroll_message()

        scrollphat.clear()
        quit()
