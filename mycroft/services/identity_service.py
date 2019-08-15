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
from os import makedirs

import json
from os.path import isfile, dirname
from time import time as get_time

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class IdentityService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        if not rt.config['use_server']:
            raise NotImplementedError('Server Disabled')

        self.identity_file = rt.paths.identity

        self.uuid = self.access_token = self.refresh_token = 'undefined'
        self.expiration = 0

        self.load()

    def is_expired(self):
        return self.refresh_token and self.expiration <= get_time()

    @staticmethod
    def translate_from_server(data):
        replacements = {
            'accessToken': 'access',
            'refreshToken': 'refresh',
            'expiration': 'expires_at'
        }
        data['expiration'] += get_time()
        return {replacements.get(k, k): v for k, v in data.items()}

    def register(self, data):
        """Registers new login data from server"""
        data = self.translate_from_server(data)
        self.assign(data)
        makedirs(dirname(self.identity_file), exist_ok=True)
        with open(self.identity_file, 'w') as f:
            json.dump(data, f)

    def assign(self, data):
        """Set identity from data"""
        if not isinstance(data, dict):
            log.error('Invalid Identity Data:', data)
            return
        try:
            self.uuid = data['uuid']
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            self.expiration = data['expires_at']
        except KeyError:
            log.exception('Loading Identity')

    def load(self):
        """Load identity from disk"""
        if isfile(self.identity_file):
            with open(self.identity_file) as f:
                data = json.load(f)
            self.assign(data)
