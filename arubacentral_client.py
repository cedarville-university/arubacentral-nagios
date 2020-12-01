#!/usr/bin/env python

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time
import argparse

tool_description = "This tool is used by collectd to get client count statistics per VC from Aruba Central"
parser = argparse.ArgumentParser(description=tool_description, add_help=True)
parser.add_argument("-g", "--group", help ="get clients from this group")
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
DEBUG = None

if args.group:
    group = args.group
if args.DEBUG:
    DEBUG = True

session = ArubaCentralAuth(ArubaCentralConfig(profile, config_path).read_config())

HOSTNAME = os.environ.get("COLLECTD_HOSTNAME")
INTERVAL = os.environ.get("COLLECTD_INTERVAL")

if not HOSTNAME:
    HOSTNAME = "localhost"
if not INTERVAL:
    INTERVAL = 60

if DEBUG:
    INTERVAL = 5

while True:
    clients = session.get_wifi_clients(group=group)
    count24 = 0
    count5 = 0
    count_os = {}
    count_conn = {}
    count_sick = 0
    for i in clients:
        if 'band' in i and i['band'] == 5:
            count5+=1
        else:
            count24+=1
        if 'os_type' in i and i['os_type'] not in count_os:
            count_os[i['os_type']] =0
        count_os[i['os_type']]+=1
        if 'connection' in i:
            for c in i['connection'].split(', '):
                if c not in count_conn:
                    count_conn[c] = 0
                count_conn[c] +=1
        if 'health' in i and i['health'] < 75:
            count_sick +=1
    print(f'PUTVAL "{HOSTNAME}/exec-client_aruba_all/gauge-arubatotal" interval={INTERVAL} N:{len(clients)}')
    print(f'PUTVAL "{HOSTNAME}/exec-client_aruba_sick/gauge-arubatotal" interval={INTERVAL} N:{count_sick}')
    for key,value in count_os.items():
        if key == '--':
            continue
        print(f'PUTVAL "{HOSTNAME}/exec-client_os_aruba_{key.replace("/","").replace(" ", "")}/gauge-arubatotal" interval={INTERVAL} N:{value}')
    for key,value in count_conn.items():
        print(f'PUTVAL "{HOSTNAME}/exec-client_connection_aruba_{key}/gauge-arubatotal" interval={INTERVAL} N:{value}')

    time.sleep(INTERVAL)
