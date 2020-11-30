#!/usr/bin/env python

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time

DEBUG = True

session = ArubaCentralAuth(ArubaCentralConfig('Default', './config').read_config())

networks = session.get_networks()
HOSTNAME = os.environ.get("COLLECTD_HOSTNAME")
INTERVAL = os.environ.get("COLLECTD_INTERVAL")

if not HOSTNAME:
    HOSTNAME = "localhost"
if not INTERVAL:
    INTERVAL = 60

if DEBUG:
    HOSTNAME = "netgraphs.cedarville.edu"
    INTERVAL = 5
while True:
    for ssid in networks:
        name = ssid['essid']
        count = session.get_wifi_clients(network=name, count_only=True)
        print(f'PUTVAL "{HOSTNAME}/exec-ssid_aruba_{name}/gauge-arubatotal" interval={INTERVAL} N:{count}')
    time.sleep(INTERVAL)
