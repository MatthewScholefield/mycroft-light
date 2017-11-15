#
# Copyright (c) 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Light
# (see https://github.com/MatthewScholefield/mycroft-light).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
from abc import ABCMeta
from copy import copy

import requests
from requests import HTTPError

from mycroft.configuration import ConfigurationManager
from mycroft.identity import IdentityManager
from mycroft.version import VersionManager

__device_info = {}


def load_device_info():
    global __device_info
    __device_info = DeviceApi().get()


class Api(metaclass=ABCMeta):
    """ Generic object to wrap web APIs """

    def __init__(self, path):
        self.path = path
        config = ConfigurationManager.get()
        config_server = config['server']
        self.url = config_server['url']
        self.version = config_server['version']
        self.identity = IdentityManager.get()
        self.old_params = None

    def request(self, params):
        self.check_token()
        self.build_path(params)
        self.old_params = copy(params)
        return self.send(params)

    def check_token(self):
        if self.identity.refresh and self.identity.is_expired():
            self.identity = IdentityManager.load()
            if self.identity.is_expired():
                self.refresh_token()

    def refresh_token(self):
        data = Api.send(super(self.__class__, self), {
            'path': 'auth/token',
            'headers': {
                'Authorization': 'Bearer ' + self.identity.refresh
            }
        })
        IdentityManager.save(data)

    def send(self, params):
        method = params.get('method', 'GET')
        headers = self.build_headers(params)
        data = self.build_data(params)
        json = self.build_json(params)
        query = self.build_query(params)
        url = self.build_url(params)
        response = requests.request(method, url, headers=headers, params=query,
                                    data=data, json=json, timeout=(3.05, 15))
        return self.get_response(response)

    def get_response(self, response):
        data = self.get_data(response)
        if 200 <= response.status_code < 300:
            return data
        elif response.status_code == 401 \
                and not response.url.endswith('auth/token'):
            self.refresh_token()
            return self.send(self.old_params)
        raise HTTPError(data, response=response)

    def get_data(self, response):
        try:
            return response.json()
        except ValueError:
            return response.text

    def build_headers(self, params):
        headers = params.get('headers', {})
        self.add_content_type(headers)
        self.add_authorization(headers)
        params['headers'] = headers
        return headers

    def add_content_type(self, headers):
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

    def add_authorization(self, headers):
        if 'Authorization' not in headers:
            headers['Authorization'] = 'Bearer ' + self.identity.access

    def build_data(self, params):
        return params.get('data')

    def build_json(self, params):
        json = params.get('json')
        if json and params['headers']['Content-Type'] == 'application/json':
            for k, v in json.items():
                if v == '':
                    json[k] = None
            params['json'] = json
        return json

    def build_query(self, params):
        return params.get('query')

    def build_path(self, params):
        path = params.get('path', '')
        params['path'] = self.path + path
        return params['path']

    def build_url(self, params):
        path = params.get('path', '')
        version = params.get('version', self.version)
        return self.url + '/' + version + '/' + path


class DeviceApi(Api):
    """ Web API wrapper for obtaining device-level information """

    def __init__(self):
        super().__init__('device')

    def get_code(self, state):
        IdentityManager.update()
        return self.request({
            'path': '/code?state=' + state
        })

    def activate(self, state, token):
        version = VersionManager.get()
        return self.request({
            'method': 'POST',
            'path': '/activate',
            'json': {
                'state': state,
                'token': token,
                'coreVersion': version['coreVersion'],
                'enclosureVersion': version['enclosureVersion']
            }
        })

    def get(self):
        """ Retrieve all device information from the web backend """
        return self.request({
            'path': '/' + self.identity.uuid
        })

    def get_settings(self):
        """ Retrieve device settings information from the web backend

        Returns:
            dict: JSON with user configuration information.
        """
        settings = self.request({'path': '/' + self.identity.uuid + '/setting'})
        loc = self.request({'path': '/' + self.identity.uuid + '/location'})
        if loc:
            settings['location'] = loc
        return settings


class STTApi(Api):
    """ Web API wrapper for performing Speech to Text (STT) """

    def __init__(self):
        super().__init__('stt')

    def stt(self, audio, language, limit):
        """ Web API wrapper for performing Speech to Text (STT)

        Args:
            audio (bytes): The recorded audio, as in a FLAC file
            language (str): A BCP-47 language code, e.g. 'en-US'
            limit (int): Maximum minutes to transcribe(?)

        Returns:
            str: JSON structure with transcription results
        """
        return self.request({
            'method': 'POST',
            'headers': {'Content-Type': 'audio/x-flac'},
            'query': {'lang': language, 'limit': limit},
            'data': audio
        })


def is_paired():
    """ Determine if this device is actively paired with a web backend

    Determines if the installation of Mycroft has been paired by the user
    with the backend system, and if that pairing is still active.

    Returns:
        bool: True if paired with backend
    """
    return bool(__device_info)
