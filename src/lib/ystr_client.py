import os, requests

from requests.exceptions import ConnectionError, ReadTimeout
from ..utility_functions import Filepath, Logger
from ..config.constants import Constants

class YstrClient:

    HTML_INDICATOR = "!doctype html"
    SECRET_REPLACEMENT = "REDACTED"

    LOADING_STATUS = "Loading"
    OFFLINE_STATUS = "Offline"
    UPDATING_STATUS = "Updating"

    LIVE_STATUS_PATH = "live_status"
    CONTRACT_PATH = "contract"

    TIMEOUT = 5 # seconds

    def __init__(self, config):
        self.config = config
        self.config_path = Filepath.get_path(os.path.join(Filepath.get_appdata_folder(), Constants.CONFIG_FILENAME))
        self.endpoint = config[Constants.ENDPOINT]
        self.name = config[Constants.NAME]
        self.secret = config[Constants.SECRET]

        # Validate existence of configs
        if None in [self.endpoint, self.name, self.secret]:
            raise Exception(f"Missing required config values! Need '{Constants.ENDPOINT}', '{Constants.NAME}', '{Constants.SECRET}' to be present in {self.config_path}.")

        # Check if endpoint is reachable and if the call succeeds
        test_response = None
        try:
            test_response = self.update_status(YstrClient.LOADING_STATUS)
        except ReadTimeout:
            raise Exception(f"Timed out while testing connection to endpoint - the configured credentials or endpoint are probably wrong! Fix them in {self.config_path} and relaunch.")

        if test_response is None or (test_response.status_code != 200) or (YstrClient.HTML_INDICATOR in str(test_response.content)):
            raise Exception(f"Failed to call the endpoint! Check your configured credentials and endpoint (in {self.config_path}) and make sure they're correct.")

    # PUT /live_status
    def update_status(self, status):
        payload = dict(zip((Constants.NAME, Constants.SECRET, Constants.STATUS), (self.name, self.secret, status)))
        return self.call(requests.put, YstrClient.LIVE_STATUS_PATH, payload)

    # GET /contract
    def get_contract(self):
        payload = dict(zip((Constants.NAME, Constants.SECRET), (self.name, self.secret)))
        response = self.call(requests.get, YstrClient.CONTRACT_PATH, payload)
        return response.json()[Constants.CONTRACT]

    # PUT /contract
    def update_contract(self, contract):
        payload = dict(zip((Constants.NAME, Constants.SECRET, Constants.CONTRACT), (self.name, self.secret, contract)))
        return self.call(requests.put, YstrClient.CONTRACT_PATH, payload)

    # Generic method for making an http call to the configured endpoint
    def call(self, method, path, payload):
        logged_body = payload.copy()
        if Constants.SECRET in logged_body:
            logged_body[Constants.SECRET] = YstrClient.SECRET_REPLACEMENT

        method_name = method.__name__.upper()
        Logger.debug(f"{method_name} /{path} request body: {logged_body}")

        try:
            response = method(f"{self.endpoint}/{path}", headers={ 'Content-Type': 'application/json' }, json=payload, timeout=YstrClient.TIMEOUT)

            Logger.debug(f"{method_name} /{path} response: {response.content} with status code {response.status_code}. Headers: {response.headers}")

            return response
        except ConnectionError as e:
            # Connection aborted
            Logger.debug(f"Connection interrupted: {e}")

            return None

    # Mark the player as offline
    def offline(self):
        return self.update_status(YstrClient.OFFLINE_STATUS)
