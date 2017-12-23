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
from abc import ABCMeta
from copy import copy
from threading import Event

import requests
from requests import HTTPError

from mycroft.util import log
from mycroft.util.misc import run_parallel
from mycroft.version import get_core_version, get_enclosure_version


class Api(metaclass=ABCMeta):
    """ Generic object to wrap web APIs """

    def __init__(self, rt, path):
        self.rt = rt
        self.path = path
        server_config = rt.config['server']
        self.url = server_config['url']
        self.version = server_config['version']
        self.old_params = None
        self.refresh_event = Event()
        self.refresh_event.set()

    def request(self, params, refresh=True):
        if refresh and self.rt.identity.is_expired():
            self.rt.identity.load()
            if self.rt.identity.is_expired():
                self.refresh_token()

        self.build_path(params)
        self.old_params = copy(params)
        return self.send(params)

    def refresh_token(self):
        if not self.refresh_event.is_set():
            self.refresh_event.wait()
            return
        self.refresh_event.clear()
        data = Api.send(super(self.__class__, self), {
            'path': 'auth/token',
            'headers': {
                'Authorization': 'Bearer ' + self.rt.identity.refresh_token
            }
        })
        self.rt.identity.register(data)
        self.refresh_event.set()

    def send(self, params):
        method = params.get('method', 'GET')
        headers = self.build_headers(params)
        data = self.build_data(params)
        json = self.build_json(params)
        query = self.build_query(params)
        url = self.build_url(params)
        log.debug(method, url, stack_offset=3)
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
            headers['Authorization'] = 'Bearer ' + self.rt.identity.access_token

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

    def __init__(self, rt):
        super().__init__(rt, 'device')

    def get_code(self, state):
        return self.request({
            'path': '/code?state=' + state
        }, refresh=False)

    def activate(self, state, token):
        return self.request({
            'method': 'POST',
            'path': '/activate',
            'json': {
                'state': state,
                'token': token,
                'coreVersion': get_core_version(),
                'enclosureVersion': get_enclosure_version()
            }
        }, refresh=False)

    def get(self):
        """ Retrieve all device information from the web backend """
        return self.request({
            'path': '/' + self.rt.identity.uuid
        })

    def get_settings(self):
        """ Retrieve device settings information from the web backend

        Returns:
            dict: JSON with user configuration information.
        """

        def get_settings():
            return self.request({'path': '/' + self.rt.identity.uuid + '/setting'}) or {}

        def get_location():
            return self.request({'path': '/' + self.rt.identity.uuid + '/location'})

        loc, settings = run_parallel([get_location, get_settings], label='Getting Settings')
        if loc:
            settings['location'] = loc
        return settings


class STTApi(Api):
    """ Web API wrapper for performing Speech to Text (STT) """

    def __init__(self, rt):
        super().__init__(rt, 'stt')

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
