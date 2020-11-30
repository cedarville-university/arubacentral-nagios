#!/usr/bin/env python

from libarubacentral import ArubaCentralAuth, ArubaCentralConfig
import logging
import argparse

tool_description = "This tool is used for checking the status of a Virtual Controller Cluster in Aruba Central"
parser = argparse.ArgumentParser(description=tool_description, add_help=True)
parser.add_argument("-V", "--vc", help ="The Name of the cluster you'd like to check")
parser.add_argument("-S", "--swarmid", help ="The swarm ID of the cluster you'd like to check")
parser.add_argument("-N", "--name", help = "the Name that corresponds to argument swarmid")
parser.add_argument("-c", "--configpath", help = "The path to the configuration folder (default: ./config)")
parser.add_argument("-W", "--warn", type=int, help = "Warning Threshold for number of APs down (default: 1)", default=1)
parser.add_argument("-C", "--crit", type=int, help = "Critical Threshold for number of APs down (default: 5)", default=5)
parser.add_argument("-P", "--profile", help="The name of the profile in the config path to use.")
parser.add_argument("-G", "--group", help="The name of the config group to check.")
parser.add_argument("-T", "--total", type=int, help="total number of expected APs in this location")
parser.add_argument("-v", "--verbose", help="Turn on error logging", action="store_true")
parser.add_argument("-vv", "--moreverbose", help="Turn on info logging", action="store_true")
parser.add_argument("-vvv", "--extraverbose", help="Turn on debug logging", action="store_true")

args = parser.parse_args()
if args.extraverbose:
    logging.basicConfig(level='DEBUG')
elif args.moreverbose:
    logging.basicConfig(level='INFO')
elif args.verbose:
    logging.basicConfig(level='ERROR')

if args.configpath:
    config_path = args.configpath
else:
    config_path = './config'

if args.profile:
    profile = args.profile
else:
    profile = 'Default'
sid = None
group = None
session = ArubaCentralAuth(ArubaCentralConfig(profile, config_path).read_config())
if args.vc and not args.swarmid:
    try:
        sid = session.get_swarm_id(args.vc)
    except RuntimeError:
        retcode = 3
        retmsg = f"VC {args.vc} not found."
        print(retmsg)
        exit(retcode)
    if args.name:
        name = "VC " + args.name
    else:
        name = "VC " + args.vc
if args.swarmid:
    sid = args.swarmid
    if args.name:
        name = "VC " + args.name
    else:
        name = "Swarm with ID: " + args.sid
if args.group:
    group = args.group
    name = args.group
down_aps = session.get_down_aps(swarm_id=sid, group=group)
down_count = len(down_aps)

if down_count >= args.crit:
    retcode = 2
    retmsg = f"{down_count} APs are down in {name} | 'down_aps'={down_count}"
elif down_count >= args.warn:
    retcode = 1
    retmsg = f"{down_count} APs are down in {name} | 'down_aps'={down_count}"
else:
    if args.total:
        total_aps = session.get_aps(swarm_id=sid, group=group)
        total_count = len(total_aps)
        if total_count < args.total:
            retcode = 3
            retmsg = f"Not enough APs in {name}. Expected {args.total}, got {total_count} | 'aps'={total_count}"
        else:
            retcode = 3
            retmsg = f"OK - {total_count} APs are up in {name} | 'aps'={total_count}"
    else:
        retcode = 0
        retmsg = f"OK - {down_count} APs are down in {name} | 'down_aps'={down_count}"

print(retmsg)
exit(retcode)