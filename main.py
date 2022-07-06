import datetime
import logging
import math
import unittest
from typing import List
import aprslib

import gps_tracker
import secrets

# This is meant to get the position of my invoxia tracker and broadcast it to the ARPS network.
# Copyright 2022 Nick Østergaard / OZ3RF


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here


class MyTracker():
    def __init__(self):
        self.username = secrets.username
        self.password = secrets.password

    def get_something(self):
        cfg = gps_tracker.Config(username=self.username, password=self.password)
        client = gps_tracker.Client(cfg)
        trackers: List[gps_tracker.Tracker] = client.get_devices(kind="tracker")
        tracker: gps_tracker.Tracker = trackers[0]
        # location = client.get_locations(tracker, not_before=datetime.datetime.now() - datetime.timedelta(minutes=15), max_count=1)
        location = client.get_locations(tracker, max_count=1)[0]
        now = datetime.datetime.now(datetime.timezone.utc)
        difftime = now - location.datetime.replace()
        print(f"\t{tracker.tracker_status.battery} % battery")
        print(f"\t{now} is now")
        print(f"\t{location.datetime} which was {difftime} ago")
        print(f"\t{location.lat} {location.lng}")
        return (location.lat, location.lng, location.datetime, tracker.tracker_status.battery)


class MyAPRS():
    def __init__(self):
        # frame = aprs.parse_frame('OZ3RF>APRS:>Hello World!')
        # a = aprs.TCP(b'OZ3RF', b'18922')
        # a.start()
        # a.send(frame)
        self.callsign = secrets.callsign
        self.passcode = aprslib.passcode(self.callsign)
        logging.basicConfig(level=logging.DEBUG)  # level=10
        self.AIS = aprslib.IS(self.callsign, passwd=self.passcode)
        #self.IS = aprslib.IS("N0CALL")

    def deg_to_dms(self, deg, type='lat'):
        decimals, number = math.modf(deg)
        d = int(number)
        m = int(decimals * 60)
        s = (deg - d - m / 60) * 3600.00
        #hundreth of minutes
        h = ( s / 60 * 100)
        compass = {
            'lat': ('N','S'),
            'lon': ('E','W')
        }
        compass_str = compass[type][0 if d >= 0 else 1]
        digits = {
            'lat': 2,
            'lon': 3,
        }
        deg_digits = digits[type]
        out = '{:0>{deg_digits}}{:02}.{:02}{}'.format(abs(d), abs(m), int(abs(h)), compass_str, deg_digits=deg_digits)
        return out

    def posdeg_to_pos_dms(self, pos):
        lat = self.deg_to_dms(pos[0], type='lat')
        lon = self.deg_to_dms(pos[1], type='lon')
        return (lat, lon)


    def callback(self, packet):
        print(packet)

    def thinghere(self, pos):
        self.AIS.connect()
        #self.AIS.consumer(self.callback, raw=False)
        #self.AIS.sendall("OZ3RF>APRS42,TCPIP*:>Hello World! With aprslib.")
        dmspos = self.posdeg_to_pos_dms(pos)
        dt = pos[2]
        hhmmss = datetime.datetime.strftime(dt, "%H%M%S")
        batpct = pos[3]
        posreport = f"OZ3RF>APRS,TCPIP*:/{hhmmss}h{dmspos[0]}/{dmspos[1]}bSigfox tracker (TESTING) Battery: {batpct}%"
        print(posreport)
        parsed = aprslib.parse(posreport)
        print(parsed)
        self.AIS.sendall(posreport)
        print("Done")


if __name__ == '__main__':
    # unittest.main()
    x = MyTracker()
    pos = x.get_something()
    a = MyAPRS()
    a.thinghere(pos)
    pass
