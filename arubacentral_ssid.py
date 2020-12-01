#!/usr/bin/env python

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time
import argparse
import threading

tool_description = "This tool is used by collectd to get client count statistics per network from Aruba Central"
parser = argparse.ArgumentParser(description=tool_description, add_help=True)
parser.add_argument("-g", "--group", help ="get networks from this group")
parser.add_argument("-n", "--network", help ="get client count for a single network")
parser.add_argument("-c", "--configpath", help = "The path to the configuration folder (default: ./config)")
parser.add_argument("-D", "--DEBUG", help ="turn on debug mode", action="store_true")
parser.add_argument("-P", "--profile", help="The name of the profile in the config path to use.")
args = parser.parse_args()

if args.configpath:
    config_path = args.configpath
else:
    config_path = './config'
if args.profile:
    profile = args.profile
else:
    profile = 'Default'

group = None
network = None
DEBUG = None

if args.group:
    group = args.group
if args.network:
    network = args.network
if args.DEBUG:
    DEBUG = True

session = ArubaCentralAuth(ArubaCentralConfig(profile, config_path).read_config())

if network:
    networks = {'essid': network}
else:
    networks = session.get_networks(group=group)

HOSTNAME = os.environ.get("COLLECTD_HOSTNAME")
INTERVAL = os.environ.get("COLLECTD_INTERVAL")

if not HOSTNAME:
    HOSTNAME = "localhost"
if not INTERVAL:
    INTERVAL = 60

if DEBUG:
    INTERVAL = 5

def print_interval():
    threading.Timer(INTERVAL, print_interval).start()
    for ssid in networks:
        name = ssid['essid']
        count = session.get_wifi_clients(network=name, count_only=True)
        print(f'PUTVAL "{HOSTNAME}/exec-ssid_aruba_{name}_clients/gauge-arubassid" interval={INTERVAL} N:{count}')
    time.sleep(int(float(INTERVAL)))

print_interval()