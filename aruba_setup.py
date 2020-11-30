from libarubacentral import ArubaCentralAuth, ArubaCentralConfig
import logging
from pprint import pprint

# logging.basicConfig(level='DEBUG')

session = ArubaCentralAuth(ArubaCentralConfig('Default', './config').read_config())

vc = "BRO"
aps = session.get_aps(limit=10, vc=vc, status='Up')
brocount = session.get_client_count(vc="BRO")
cfacount = session.get_client_count(vc="Library")
#allcount = session.get_client_count(group='Cedarville University')
#reservedcount = session.get_client_count(network='cu-reserved')
broclients = session.get_wifi_clients(vc="BRO", count_only=True)
reservedclients = session.get_wifi_clients(network='cu-reserved', count_only=True)
pprint(broclients)


