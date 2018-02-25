#!/usr/bin/env python

# requires: netifaces for looking up IP in readable way
# requires: requests human readable HTTP requests

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

try:
    import datetime
except ImportError:
    exit("This script requires the datetime module\nInstall with: sudo pip install datetime")


class MainApp:

    check_days = 3               # 予報を表示する日数
    lotate_time_sec = 0.2        # スクロールの更新間隔(sec)
    update_time_sec = 60 * 60    # 予報の更新間隔(sec)
    local_time_hour = 9          # タイムゾーン(JP:+9h)
    fahrenheit_or_celsius = 'c'  # 摂氏か華氏か切り替え(c か f)

    item = ""
    title = ""
    output = ""
    weather = ""
    get_date = ""
    pub_date = ""
    update_date = ""
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
            index_format = val.find("format")
            val = val[:index_format - 1] + "%20and%20u%3D%22" + self.fahrenheit_or_celsius + "%22" + val[index_format - 1:]
            
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
        self.time_adjustment(self.local_time_hour)
        self.pub_date = self.weather["query"]["results"]["channel"]["item"]["pubDate"]
        self.title = self.weather["query"]["results"]["channel"]["item"]["title"]
        self.output = ""

        # Feel free to pick out other data here, for the scrolling message
        for x in range(0, days):
            self.item = self.weather["query"]["results"]["channel"]["item"]["forecast"][x]
            if self.fahrenheit_or_celsius == 'c':
                self.output = self.output + " " + self.item["day"] + ": " + self.item["text"] + "  -L: " + self.item["low"] + "C  -H: " + self.item["high"] + "C  "
            else:
                self.output = self.output + " " + self.item["day"] + ": " + self.item["text"] + "  -L: " + self.item["low"] + "F  -H: " + self.item["high"] + "F  "

    def time_adjustment(self, time_hour):
        self.get_date = datetime.datetime.strptime(self.weather["query"]["created"][:-1], '%Y-%m-%dT%H:%M:%S')
        self.get_date += datetime.timedelta(hours=time_hour)
        self.get_date = self.get_date.strftime('%Y/%m/%d %H:%M:%S')

    def add_get_weather_date_output(self):
        self.output += " Get: " + self.get_date

    def add_get_weather_title_output(self):
        self.output += " <<< " + self.title + " >>> "

    def get_weather_info(self):
        print("")
        print(" --- Weather Info ---")
        print("       Get: " + self.get_date)
        print("   Updated: " + self.pub_date)
        print("  Location: " + self.location_string)
        print("     Title: " + self.title)
        print("      Data: " + self.output)
        # print("     Debug: " + str(self.weather))
        print(" --------------------")

    def scroll_message(self):

        time_count_par_sec = 1 / self.lotate_time_sec
        time_count_limit = time_count_par_sec * self.update_time_sec
        time_count = time_count_limit
        while True:
            try:
                if time_count >= time_count_limit:
                    print("Update...")
                    self.get_weather_days(self.check_days)
                    self.get_weather_info()
                    self.add_get_weather_title_output()
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