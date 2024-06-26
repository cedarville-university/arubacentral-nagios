#!/usr/bin/env python
import requests.exceptions

from libarubacentral import ArubaCentralConfig, ArubaCentralAuth
import os
import time
import argparse
import logging
import datetime


tool_description = "This tool is used by collectd to get client count statistics per VC from Aruba Central"
parser = argparse.ArgumentParser(description=tool_description, add_help=True)
parser.add_argument("-g", "--group", help ="get clients from this group")
parser.add_argument("-c", "--configpath", help = "The path to the configuration folder (default: ./config)")
parser.add_argument("-D", "--DEBUG", help ="turn on debug mode", action="store_true")
parser.add_argument("-P", "--profile", help="The name of the profile in the config path to use.")
parser.add_argument("-i", "--interval", type=float, help="The interval at which to repeat the statistic (in seconds)")
args = parser.parse_args()

if args.configpath:
    config_path = args.configpath
else:
    config_path = './config'
if args.profile:
    profile = args.profile
else:
    profile = 'Default'

logging.basicConfig(filename=config_path + "/arubacentral_client.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    level=logging.DEBUG)
log = logging.getLogger("arubacentral_client")
# ConsoleOutputHandler = logging.StreamHandler()
# log.addHandler(ConsoleOutputHandler)
# log.setLevel(logging.INFO)

group = None
DEBUG = None
max_results = 1000  # << hard-coded because this is an Aruba limit
networks = list()
swarms = list()

if args.group:
    group = args.group
if args.DEBUG:
    DEBUG = True

if DEBUG:
    log.setLevel(logging.DEBUG)
log.debug("starting arubacentral client counter")
session = ArubaCentralAuth(ArubaCentralConfig(profile, config_path, DEBUG).read_config())
log.debug(f"got Session token")
try:
    networks = session.get_networks(group=group)
    log.debug(f"got {len(networks)} networks")
    swarms = session.get_swarms(group=group)
    log.debug(f"got {len(swarms)} swarms")
except RuntimeError as e:
    print("Request failed: " + str(e))
    exit(1)
swarm_id_lookup = {}
for n in swarms:
    swarm_id_lookup[n['swarm_id']] = n['name']
log.debug('finished building swarm lookup')
HOSTNAME = os.environ.get("COLLECTD_HOSTNAME")
INTERVAL = os.environ.get("COLLECTD_INTERVAL")
if args.interval:
    INTERVAL = args.interval

if not HOSTNAME:
    HOSTNAME = "localhost"
if not INTERVAL:
    INTERVAL = 60

if DEBUG:
    INTERVAL = 5
log.debug(f"running every {INTERVAL} seconds, to host {HOSTNAME}")
while True:
    try:
        start = datetime.datetime.now()
        page = 1
        clients = session.get_wifi_clients(group=group, timeout=90)
        log.debug(f'fetched page {page} of {len(clients)} clients')
        all_clients = clients
        while len(clients) == max_results:
            clients = session.get_wifi_clients(group=group, offset=(page * 1000), timeout=90)
            all_clients = all_clients + clients
            log.debug(f'fetched page {page} of {len(clients)} clients, total so far {len(all_clients)}'
                      f' (offset: {page*1000})')
            page += 1

        count24 = 0
        count5 = 0
        count6 = 0
        count_os = dict()
        count_conn = dict()
        count_sick = 0
        count_ssid = dict()
        count_vc = dict()
        log.debug(f"beginning counts for {len(all_clients)}")
        client_index = 0
        for i in all_clients:
            if 'band' in i and i['band'] == 5:
                count5 += 1
            elif 'band' in i and i['band'] == 6:
                count6 += 1
            else:
                count24 += 1
            if 'os_type' in i and i['os_type'] not in count_os:
                count_os[i['os_type']] = 0
            if i['os_type'] == '--':
                if not 'Unclassified Device' in count_os:
                    count_os['Unclassified Device'] = 0
                count_os['Unclassified Device'] += 1
            else:
                count_os[i['os_type']] += 1
            if 'connection' in i:
                for c in i['connection'].split(', '):
                    if c not in count_conn:
                        count_conn[c] = 0
                    count_conn[c] += 1
            if 'health' in i and i['health'] < 75:
                count_sick += 1
            if 'network' in i and i['network']:
                if i['network'] not in count_ssid:
                    count_ssid[i['network']] = 0
                count_ssid[i['network']] += 1
            if 'swarm_id' in i and i['swarm_id'] and swarm_id_lookup.get(i['swarm_id']):
                vc = swarm_id_lookup[i['swarm_id']]
                if vc not in count_vc:
                    count_vc[vc] = 0
                count_vc[vc] += 1
            elif 'group' in i and i['group']:
                group_name = i['group']
                if group_name not in count_vc:
                    count_vc[group_name] = 0
                count_vc[group_name] += 1
            elif 'group_name' in i and i['group_name']:
                group_name = i['group_name']
                if group_name not in count_vc:
                    count_vc[group_name] = 0
                count_vc[group_name] += 1
            client_index += 1
            if client_index > 0 and client_index % 1000 == 0:
                log.debug(f"counted {client_index} clients so far...")
        print(f'PUTVAL "{HOSTNAME}/exec-aruba_all_clients/gauge-arubatotal" interval={INTERVAL} N:{len(all_clients)}')
        print(f'PUTVAL "{HOSTNAME}/exec-aruba_sick_clients/gauge-arubasick" interval={INTERVAL} N:{count_sick}')
        for key, value in count_os.items():
            print(f'PUTVAL "{HOSTNAME}/exec-os_aruba_{key.replace("/","").replace(" ", "")}_clients/gauge-arubaos" interval={INTERVAL} N:{value}')
        for key, value in count_ssid.items():
            print(f'PUTVAL "{HOSTNAME}/exec-ssid_aruba_{key}_clients/gauge-arubassid" interval={INTERVAL} N:{value}')
        for key, value in count_vc.items():
            print(f'PUTVAL "{HOSTNAME}/exec-vc_aruba_{key}_clients/gauge-arubavc" interval={INTERVAL} N:{value}')
        for key, value in count_conn.items():
            print(f'PUTVAL "{HOSTNAME}/exec-connection_aruba_{key}_clients/gauge-arubaconn" interval={INTERVAL} N:{value}')
        print(f'PUTVAL "{HOSTNAME}/exec-aruba_5g_clients/gauge-arubaband" interval={INTERVAL} N:{count5}')
        print(f'PUTVAL "{HOSTNAME}/exec-aruba_6g_clients/gauge-arubaband" interval={INTERVAL} N:{count6}')
        print(f'PUTVAL "{HOSTNAME}/exec-aruba_24g_clients/gauge-arubaband" interval={INTERVAL} N:{count24}')
    except RuntimeError as e:
        print("Request failed: " + str(e))
    except requests.exceptions.Timeout as f:
        print("Request failed: " + str(f))
    elapsed = datetime.datetime.now() - start
    if elapsed.seconds < INTERVAL:
        time.sleep(float(INTERVAL-elapsed.seconds))
