# arubacentral-nagios
A library to interact with Aruba Central (Based on Michael Rose's [PyArubaCentral](https://pypi.org/project/pyarubacentral/)), with the goal of being able to check Aruba Central VC's and Access Points using Nagios Core

You can use the ArubaCentralConfig and ArubaCentralAuth classes from libarubacentral.py to create your own scripts that authenticate and interact with Aruba Central automatically. 

There are a few methods inside the ArubaCentralAuth class that already get useful things from the Aruba Central API. I welcome PRs with additional functionality added to that. 

The aruba_setup.py file has a few examples of how to use the methods to retrieve information in a pythonic way.

Check_aruba_central_aps.py is a nagios plugin that allows you to check AC Clusters for down APs using Nagios Core.
