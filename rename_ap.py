from libarubacentral import ArubaCentralAuth, ArubaCentralConfig
from sys import argv
import csv

session = ArubaCentralAuth(ArubaCentralConfig('Default', './config').read_config())

filename = argv[1]
ap_list = list()
with open(filename, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        ap_list.append(row)
result = list()

for i in ap_list:
    if i['Type'] != 'AP':
        continue
    try:
        session.name_ap(i['AP Name'], i['Serial Number'])
        print(f"Success: {i['Serial Number']} --> {i['AP Name']}")
    except RuntimeError as e:
        print(f"Failed: {i['Serial Number']} --> {i['AP Name']}\n\t {str(e)}")
