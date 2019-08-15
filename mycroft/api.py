# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
from threading import Event, Lock

import requests
from requests import RequestException

from mycroft.util import log
from mycroft.util.parallel import run_parallel
from mycroft.version import get_core_version, get_enclosure_version


class Api(metaclass=ABCMeta):
    """ Generic object to wrap web APIs """

    def __init__(self, rt, path):
        self.rt = rt
        self.path = path
        self.url = rt.config['server_url']
        self.old_params = None
        self.refresh_lock = Lock()

    def request(self, params, refresh=True):
        if refresh and self.rt.identity.is_expired():
            self.rt.identity.load()
            if self.rt.identity.is_expired():
                self.refresh_token()

        self.build_path(params)
        self.old_params = copy(params)
        return self.send(params)

    def refresh_token(self):
        if self.refresh_lock.locked():
            with self.refresh_lock:
                return
        with self.refresh_lock:
            data = Api.send(super(self.__class__, self), {
                'path': 'auth/token',
                'headers': {
                    'Authorization': 'Bearer ' + self.rt.identity.refresh_token
                }
            })
            self.rt.identity.register(data)

    def send(self, params):
        method = params.get('method', 'GET')
        headers = self.build_headers(params)
        data = self.build_data(params)
        json = self.build_json(params)
        query = self.build_query(params)
        url = self.build_url(params)
        try:
            response = requests.request(method, url, headers=headers, params=query,
                                        data=data, json=json, timeout=(3.05, 5))
        except RequestException as e:
            response = e
        else:
            log.debug(method, url, response.status_code, stack_offset=3)
        if isinstance(response, Exception):
            raise ConnectionError('Failed to {} {}: {}'.format(method, url, response))
        return self.get_response(response)

    def get_response(self, response):
        data = self.get_data(response)
        if 200 <= response.status_code < 300:
            return data
        elif response.status_code == 401 \
                and not response.url.endswith('auth/token'):
            self.refresh_token()
            return self.send(self.old_params)
        raise ConnectionError(data)

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
        return self.url + '/' + params.get('path', '')


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
                'platform': self.rt.config['interfaces']['faceplate']['platform'],
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
            out = self.request({'path': '/' + self.rt.identity.uuid + '/setting'})
            return out or {}

        def get_location():
            return self.request({'path': '/' + self.rt.identity.uuid + '/location'})

        loc, settings = run_parallel([get_location, get_settings], label='Getting Settings')
        if not settings:
            raise ConnectionError('Could not request settings from server')
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
            limit (int): Maximum minutes to _transcribe(?)

        Returns:
            str: JSON structure with transcription results
        """
        return self.request({
            'method': 'POST',
            'headers': {'Content-Type': 'audio/x-flac'},
            'query': {'lang': language, 'limit': limit},
            'data': audio
        })
