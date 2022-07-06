#!/usr/bin/env python3
import datetime
import logging
import math
import random
import time
import unittest
from typing import List, Optional
import aprslib

import gps_tracker
from gps_tracker.client.datatypes import TrackerIcon

import secrets

log = logging.getLogger("main")
log.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)


# This is meant to get the position of my invoxia tracker and broadcast it to the ARPS network.
# Copyright 2022 Nick Østergaard / OZ3RF


class MyTestCase(unittest.TestCase):
    def test_icon_detect(self):
        instance = MyAPRS()
        # Check we can do a correct conversion
        self.assertEqual(instance.icon_detect(TrackerIcon.HELICOPTER), ('/', 'X'))
        # Some TrackerIcon not in the conversion list, i.e. fallback APRS icon
        self.assertEqual(instance.icon_detect(TrackerIcon.WOMAN), ('/', ':'))

class MyTracker:
    def __init__(self):
        self.username = secrets.username
        self.password = secrets.password

    def get_something(self):
        cfg = gps_tracker.Config(username=self.username, password=self.password)
        client = gps_tracker.Client(cfg)
        trackers: List[gps_tracker.Tracker] = client.get_devices(kind="tracker")
        tracker: gps_tracker.Tracker = trackers[0]
        # location = client.get_locations(tracker, not_before=datetime.datetime.now() - datetime.timedelta(minutes=15), max_count=1)
        location = client.get_locations(tracker, max_count=1)[0]  # TODO: Assumes we only have one tracker
        now = datetime.datetime.now(datetime.timezone.utc)
        difftime = now - location.datetime.replace()
        log.info(f"\t{tracker.tracker_status.battery} % battery")
        log.info(f"\t{now} is now")
        log.info(f"\t{location.datetime} which was {difftime} ago")
        log.info(f"\t{location.lat} {location.lng}")
        return location, tracker


class MyAPRS:
    def __init__(self):
        self.callsign = secrets.callsign
        self.passcode = aprslib.passcode(self.callsign)
        self.AIS = aprslib.IS(callsign=self.callsign, passwd=self.passcode)
        self.posreport: Optional[str] = None

    def deg_to_dmh(self, deg, type='lat'):
        """
        Converts signed decimal degrees to degree-minutes-hundredths compatible with the APRS spec ddmmhh notation.
        """
        decimals, number = math.modf(deg)
        d = int(number)
        m = int(decimals * 60)
        s = (deg - d - m / 60) * 3600.00
        #hundredths of minutes
        h = ( s / 60 * 100)
        compass = {
            'lat': ('N', 'S'),
            'lon': ('E', 'W')
        }
        compass_str = compass[type][0 if d >= 0 else 1]
        digits = {
            'lat': 2,
            'lon': 3,
        }
        deg_digits = digits[type]
        out = '{:0>{deg_digits}}{:02}.{:02}{}'.format(abs(d), abs(m), int(abs(h)), compass_str, deg_digits=deg_digits)
        return out

    def posdeg_to_posdmh(self, in_lat, in_lon):
        lat = self.deg_to_dmh(in_lat, type='lat')
        lon = self.deg_to_dmh(in_lon, type='lon')
        return lat, lon

    def icon_detect(self, ti: TrackerIcon):
        icon_table = {
            TrackerIcon.BIKE: ('/', 'b'),
            TrackerIcon.HELICOPTER: ('/', 'X'),
            TrackerIcon.BACKPACK: ('/', '"'),
            TrackerIcon.TENT: ('/', ';'),
            TrackerIcon.ANTENNA: ('/', 'r'),
        }
        if ti in icon_table:
            return icon_table[ti]
        else:
            # Fallback icon
            return '/', ':'

    def create_position_msg(self, location: gps_tracker.TrackerData, tracker: gps_tracker.Tracker, msg: str = 'Sigfox tracker (TESTING)'):
        """
        This takes location and tracker information to generate an appropriate position message.
        """
        dmhpos = self.posdeg_to_posdmh(location.lat, location.lng)
        dt = location.datetime
        hhmmss = datetime.datetime.strftime(dt, "%H%M%S")
        primary, alternate = self.icon_detect(tracker.tracker_config.icon)
        batpct = tracker.tracker_status.battery
        self.posreport = f"{self.callsign}>APRS,TCPIP*:/{hhmmss}h{dmhpos[0]}{primary}{dmhpos[1]}{alternate}{msg} [Battery: {batpct}%]"

        log.debug(self.posreport)
        log.debug(aprslib.parse(self.posreport))

    def broadcast(self):
        self.AIS.connect()
        self.AIS.sendall(self.posreport)
        self.AIS.close()


class SuperClass:
    def __init__(self):
        self.tracker: Optional[gps_tracker.Tracker] = None
        self.location: Optional[gps_tracker.TrackerData] = None
        try:
            self.fetch_data()
            self.broadcast_data()
        except:
            log.info("Expcetions on first runthrough, but continuing...")
        self.schedule()

    def fetch_data(self):
        trk_cls = MyTracker()
        self.location, self.tracker = trk_cls.get_something()

    def broadcast_data(self):
        aprs_cls = MyAPRS()
        aprs_cls.create_position_msg(self.location, self.tracker)
        aprs_cls.broadcast()

    def schedule(self):
        log.info("Running on a schedule...")
        jitter = 10
        waittime = 60 * 5
        try:
            while True:
                slt = random.randint(waittime, waittime+jitter)
                log.debug(f"Sleep time: {slt}")
                time.sleep(slt)
                self.fetch_data()
                self.broadcast_data()
        except KeyboardInterrupt:
            pass
            print("\n")
            log.info("Exiting.")

if __name__ == '__main__':
    #unittest.main()
    SuperClass()
    log.info("Done.")