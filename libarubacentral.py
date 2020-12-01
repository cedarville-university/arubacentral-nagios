import requests
import json
import yaml
import os
import logging
from datetime import datetime, timedelta


class ArubaCentralConfig:
    def __init__(self, profile, configpath):
        self.profile = profile
        self.configpath = configpath

    def read_accounts(self, account):
        data = dict()
        if os.path.isfile(self.configpath + "/accounts.yml"):
            with open("/accounts.yml", 'r') as ymlfile:
                data = yaml.load(ymlfile, Loader=yaml.FullLoader)
        else:
            print(
                "Please read the README file and create the accounts.yml file using the sample.accounts.yml as a guide")
        return data

    def read_config(self) -> dict:
        data = dict()
        if os.path.isfile(self.configpath + "/config.yml"):
            accounts = dict()
            regions = dict()
            with open(self.configpath + "/config.yml", 'r') as ymlfile:
                cfgdata = yaml.load(ymlfile, Loader=yaml.FullLoader)

            # Get list of Centrla accounts
            if os.path.isfile(self.configpath + "/accounts.yml"):
                with open(self.configpath + "/accounts.yml", 'r') as ymlfile:
                    accounts = yaml.load(ymlfile, Loader=yaml.FullLoader)
            else:
                print(
                    "Please read the README file and create the accounts.yml file using the sample.accounts.yml as a guide")

            # Get Central regions
            if os.path.isfile(self.configpath + "/regions.yml"):
                with open(self.configpath + "/regions.yml", 'r') as ymlfile:
                    regions = yaml.load(ymlfile, Loader=yaml.FullLoader)
            else:
                print(
                    "Please read the README file and create the regions.yml file using the sample.regions.yml as a guide")

            data = {}
            try:
                data.update(cfgdata[self.profile])
            except Exception:
                logging.error(f'Profile not found. Please create a profile in {self.configpath}')
                exit(0)
            data.update(accounts[cfgdata[self.profile]['user_account']])
            data.update({"url": regions[cfgdata[self.profile]['region']]['url']})
            data.update({"profile": self.profile})
            data.update({"configpath": self.configpath})
        else:
            print("Please read the README file and create the config.yml file using the sample.config.yml as a guide")
        return data


class ArubaCentralAuth:
    def __init__(self, cfgdata):
        self.cfgdata = cfgdata
        self.profile = cfgdata['profile']
        self.access_token = None

    def get_login(self) -> dict:
        csrftoken = 'uninitialized'
        csession = 'uninitialized'
        auth_url = self.cfgdata['url'] + "/oauth2/authorize/central/api/login"
        params = {"client_id": self.cfgdata['client_id']}
        headers = {"Content-Type": "application/json"}
        data = {"username": self.cfgdata['username'], "password": self.cfgdata['password']}
        s = requests.Session()
        r = s.post(auth_url, headers=headers, params=params, data=json.dumps(data), verify=True, timeout=10)
        if r.status_code == 200:
            for i in r.cookies:
                if i.name == "csrftoken":
                    csrftoken = i.value
                if i.name == "session":
                    csession = i.value
        else:
            print("ERROR CODE: " + str(r.status_code))
            print("ERORR Detail: " + str(r.text))
            print(
                "\nERROR : The information in the config or accounts YAML files are incorrect.\n" + \
                "ERROR : Please check your configuration and Aruba Central settings are correct\n")

        logincookies = {
            "csrftoken": csrftoken,
            "csession": csession
        }

        return logincookies

    def get_authcode(self, login_data) -> str:
        authcode = 'uninitialized'
        auth_url = self.cfgdata['url'] + "/oauth2/authorize/central/api"
        csrftoken = login_data['csrftoken']
        csession = login_data['csession']
        headers = {"Content-Type": "application/json",
                   "X-CSRF-TOKEN": csrftoken,
                   "Cookie": "session=" + csession}
        params = {"client_id": self.cfgdata['client_id'], "response_type": "code", "scope": "all"}
        data = {"customer_id": str(self.cfgdata['customer_id'])}
        s = requests.Session()
        result = s.post(auth_url, headers=headers, params=params,
                        data=json.dumps(data), verify=True, timeout=10)
        if result.status_code == 200:
            tmp = json.loads(result.text)
            authcode = tmp['auth_code']
        else:
            print("status code : " + str(result.status_code))
            print("text : " + str(result.text))
            exit(0)

        logging.debug("authcode: %s", authcode)
        return authcode

    def get_access_token(self, authcode) -> dict:
        token_url = self.cfgdata['url'] + "/oauth2/token"
        data = dict()
        headers = dict()
        tokens = dict()
        params = {"client_id": self.cfgdata['client_id'], "client_secret": self.cfgdata['client_secret'],
                  "grant_type": "authorization_code", "code": authcode}
        r = requests.post(token_url, headers=headers, params=params,
                          data=json.dumps(data), verify=True, timeout=10)
        if r.status_code == 200:
            tokens = json.loads(r.text)
            #
            # Set expire time less than 120 seconds for a buffer
            #
            expires_at_dt = datetime.now() + timedelta(0, (tokens['expires_in'] - 120))
            expires_at_epoc = expires_at_dt.timestamp()
            tokens.update({'expires_at': expires_at_epoc})
            self.access_token = tokens
            with open(self.cfgdata['configpath'] + "/tokens/" + self.profile + ".token.json", 'w') as newtokenfile:
                newtokenfile.write(json.dumps(tokens))
        else:
            print("STATUS CODE: {} \nDetail: {}".format(str(r.status_code), str(r.text)))
        return tokens

    def retrieve_stored_token(self):
        data = dict()
        if os.path.exists(self.cfgdata['configpath'] + "/tokens/" + self.profile + ".token.json"):
            with open(self.cfgdata['configpath'] + "/tokens/" + self.profile + ".token.json", 'r') as existingtokenfile:
                data = json.loads(existingtokenfile.read())
        else:
            print(f"No stored token for profile {self.profile}")
        return data

    def refresh_access_token(self, access_token: dict=None) -> dict:
        if not access_token:
            access_token = self.access_token
        new_token = dict()
        token_url = self.cfgdata['url'] + "/oauth2/token"
        data = {}
        headers = {}
        params = {"client_id": self.cfgdata['client_id'], "client_secret": self.cfgdata['client_secret'],
                  "grant_type": "refresh_token", "refresh_token": access_token['refresh_token']}
        r = requests.post(token_url, headers=headers, params=params,
                          data=json.dumps(data), verify=True, timeout=10)
        if r.status_code == 200:
            new_token = json.loads(r.text)
            #
            # Set expire time less than 120 seconds for a buffer
            #
            expires_at_dt = datetime.now() + timedelta(0, (new_token['expires_in'] - 120))
            expires_at_epoc = expires_at_dt.timestamp()
            new_token.update({'expires_at': expires_at_epoc})
            self.access_token = new_token
            with open(self.cfgdata['configpath'] + "/tokens/" + self.profile + ".token.json", 'w') as newtokenfile:
                newtokenfile.write(json.dumps(new_token))
        else:
            print("STATUS CODE: {} \nDetail: {}".format(str(r.status_code), str(r.text)))

        return new_token

    def token_expired(self, access_token: dict = None) -> bool:
        if not access_token:
            access_token = self.access_token
        expires_at = datetime.fromtimestamp(access_token['expires_at'])
        if datetime.now() > expires_at:
            logging.debug("Access token expired, refresh requested.")
            return True
        else:
            logging.debug("Access token valid. Expires at: %s ", expires_at)
            return False

    def authenticate(self):
        if not self.access_token:
            logging.debug(f"Access token not cached. retrieving from {self.cfgdata['configpath']+'/tokens/' + self.profile + '.token.json'}")
            self.access_token = self.retrieve_stored_token()
        if not self.access_token:
            logging.debug(f"Access token not stored. Generating a new token.")
            cookies = self.get_login()
            code = self.get_authcode(cookies)
            self.get_access_token(code)
        if self.token_expired():
            self.refresh_access_token()
        if not self.access_token:
            raise RuntimeError('Token problem. No token stored, or token still expired after refresh.')

    def get_user_account_list(self, access_token: dict = None):
        return self._get_api("/platform/rbac/v1/users", access_token)

    def get_aps(self, access_token: dict = None, limit: int = 100, status: str = None, vc: str = None,
                group: str = None, client_count: bool = None, label: str = None, swarm_id=None):
        url = "/monitoring/v1/aps"
        if limit:
            url = self._add_arg(url, f"limit={str(limit)}")
        if status:
            url = self._add_arg(url, f"status={status}")
        if swarm_id:
            url = self._add_arg(url, f"swarm_id={swarm_id}")
        elif vc:
            url = self._add_arg(url, f"swarm_id={self.get_swarm_id(vc, access_token=access_token)}")
        if group:
            url = self._add_arg(url, f"group={group}")
        if client_count:
            url = self._add_arg(url, f"calculate_client_count=true")
        if label:
            url = self._add_arg(url, f"label={label}")
        logging.debug(f"getting aps: {url}")
        return self._get_api(url, access_token)['aps']

    def get_swarm_id(self, name, access_token: dict=None) -> str:
        data = self._get_api('/monitoring/v1/swarms', access_token)
        for swarm in data['swarms']:
            if name.lower() in swarm['name'].lower():
                return swarm['swarm_id']
        raise RuntimeError(f"No swarm found with name {name}")

    def get_ap(self, serial, access_token: dict = None):
        data = self._get_api(f'/monitoring/v1/aps/{serial}', access_token)
        return data

    def _get_api(self, url, access_token: dict=None) -> dict:
        if not access_token:
            self.authenticate()
            access_token = self.access_token
        api_data = dict()
        this_access_token = access_token['access_token']
        token_url = self.cfgdata['url'] + url
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        data = {
            'access_token': this_access_token
        }
        r = requests.get(token_url, headers=headers, data=json.dumps(data), verify=True, timeout=10)
        if r.status_code == 200:
            api_data = json.loads(r.text)
        else:
            print("STATUS CODE: {} \nDetail: {}".format(str(r.status_code), str(r.text)))
        return api_data

    @staticmethod
    def _add_arg(url:str, arg: str):
        if '?' not in url:
            url += '?'
        else:
            url += '&'
        url += arg
        return url

    def get_down_aps(self, vc = None, group = None, access_token=None, swarm_id = None):
        down_list = self.get_aps(status='Down', vc=vc, group=group, access_token=access_token, swarm_id=swarm_id)
        return down_list

    def get_client_count(self, vc = None, group=None, network=None, label=None, access_token=None, swarm_id=None):
        url = '/monitoring/v1/clients/count'
        if swarm_id:
            url = self._add_arg(url, f"swarm_id={swarm_id}")
        elif vc:
            url = self._add_arg(url, f"swarm_id={self.get_swarm_id(vc, access_token=access_token)}")
        if group:
            url = self._add_arg(url, f"group={group}")
        if label:
            url = self._add_arg(url, f"label={label}")
        if network:
            url = self._add_arg(url, f"network={network}")
        return self._get_api(url, access_token=access_token)['count']

    def get_wifi_clients(self, vc = None, group=None, network=None, label=None, access_token=None, count_only=False,
                         limit=1000, band=None):
        url = '/monitoring/v1/clients/wireless'
        if limit:
            url = self._add_arg(url, f"limit={str(limit)}")
        if vc:
            url = self._add_arg(url, f"swarm_id={self.get_swarm_id(vc, access_token=access_token)}")
        if group:
            url = self._add_arg(url, f"group={group}")
        if label:
            url = self._add_arg(url, f"label={label}")
        if network:
            url = self._add_arg(url, f"network={network}")
        if band:
            url = self._add_arg(url, f"band={band}")
        url = self._add_arg(url, 'calculate_total=true')
        if count_only:
            return self._get_api(url, access_token=access_token)['count']
        else:
            return self._get_api(url, access_token=access_token)['clients']

    def get_networks(self, access_token: dict=None, group=None):
        url = '/monitoring/v1/networks'
        if group:
            url = self._add_arg(url, f"group={group}")
        return self._get_api(url, access_token=access_token)['networks']

    def get_vcs(self, access_token: dict=None, group=None):
        url = '/monitoring/v1/swarms'
        if group:
            url = self._add_arg(url, f"group={group}")
        return self._get_api(url, access_token=access_token)['swarms']
