#!/usr/bin/env python

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time
import argparse

tool_description = "This tool is used by collectd to get client count statistics per VC from Aruba Central"
parser = argparse.ArgumentParser(description=tool_description, add_help=True)
parser.add_argument("-g", "--group", help ="get clients from this group")
parser.add_argument("-D", "--DEBUG", help ="turn on debug mode", action="store_true")
args = parser.parse_args()

group = None
DEBUG = None

if args.group:
    group = args.group
if args.DEBUG:
    DEBUG = True

session = ArubaCentralAuth(ArubaCentralConfig('Default', './config').read_config())

vcs = session.get_vcs(group=group)
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
