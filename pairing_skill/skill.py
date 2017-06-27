#
# Copyright (c) 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Simple
# (see https://github.com/MatthewScholefield/mycroft-simple).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# 'License'); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import time
from threading import Timer
from uuid import uuid4

from requests import HTTPError

from mycroft.api import DeviceApi, is_paired
from mycroft.identity import IdentityManager
from mycroft.mycroft_skill import MycroftSkill


class PairingSkill(MycroftSkill):
    DELAY = 10
    EXPIRATION = 72000  # 20 hours

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = DeviceApi()
        self.data = None
        self.last_request = None
        self.state = str(uuid4())
        self.register_intent('pair', self.on_pair_intent)
        self.check_paired()

    def check_paired(self):
        if not is_paired():
            self.create_new_code()
            self.add_action('code', self.data.get('code'))
            self.send_results('pair')

    def is_paired(self):
        try:
            device = self.api.get()
        except:
            device = None
        return device is not None

    def on_pair_intent(self, intent_data):
        if is_paired():
            self.set_action('pair.complete')
        elif self.data and self.last_request < time.time():
            self.add_result('code', self.data.get('code'))
        else:
            self.create_new_code()
            self.add_result('code', self.data.get('code'))
            self._create_activator()

    def create_new_code(self):
        self.last_request = time.time() + self.EXPIRATION
        self.data = self.api.get_code(self.state)

    def on_activate(self):
        try:
            # wait for a signal from the backend that pairing is complete
            token = self.data.get('token')
            login = self.api.activate(self.state, token)

            IdentityManager.save(login)
            IdentityManager.update(login)
            self.add_action('pair.complete')
        except HTTPError:
            if self.last_request < time.time():
                self.data = None
                self.on_pair_intent()
            else:
                self._create_activator()

    def _create_activator(self):
        activator = Timer(self.DELAY, self.on_activate)
        activator.daemon = True
        activator.start()
