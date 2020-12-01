#!/usr/bin/env python

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time

DEBUG = True
GROUP = None

session = ArubaCentralAuth(ArubaCentralConfig('Default', './config').read_config())

vcs = session.get_vcs(GROUP)
HOSTNAME = os.environ.get("COLLECTD_HOSTNAME")
INTERVAL = os.environ.get("COLLECTD_INTERVAL")

if not HOSTNAME:
    HOSTNAME = "localhost"
if not INTERVAL:
    INTERVAL = 60

if DEBUG:
    INTERVAL = 5

while True:
    for vc in vcs:
        name = vc['name']
        count = session.get_wifi_clients(vc=name, count_only=True)
        print(f'PUTVAL "{HOSTNAME}/exec-vc_aruba_{name}/gauge-arubatotal" interval={INTERVAL} N:{count}')
    time.sleep(INTERVAL)
