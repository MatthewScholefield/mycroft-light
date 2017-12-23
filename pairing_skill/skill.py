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

import time
from threading import Timer
from uuid import uuid4

from requests import HTTPError

from mycroft import MycroftSkill
from mycroft.api import DeviceApi
from mycroft.util import log


class PairingSkill(MycroftSkill):
    DELAY = 10
    EXPIRATION = 20 * 60 * 60  # 20 hours

    def __init__(self):
        super().__init__()
        self.api = DeviceApi(self.rt)
        self.data = None
        self.expire_time = None
        self.state = str(uuid4())
        self.register_intent('pair', self.pair_device)
        self.check_paired()

    def check_paired(self):
        if not self.rt.device_info:
            self.pair_device()
            self.trigger_action('pair')
            self.create_activator()

    def pair_device(self):
        if self.rt.device_info:
            self.set_action('pair.complete')
            return 0.6
        elif self.data and self.expire_time > time.time():
            self.add_result('code', self.data['code'])
            return 0.85
        else:
            self.create_new_code()
            self.add_result('code', self.data['code'])
            return 0.8

    def create_new_code(self):
        self.expire_time = time.time() + self.EXPIRATION
        self.data = self.api.get_code(self.state)

    def on_activate(self):
        try:
            # wait for a signal from the backend that pairing is complete
            token = self.data.get('token')
            login = self.api.activate(self.state, token)

            self.rt.identity.register(login)
            self.set_action('pair.complete')
        except HTTPError:
            self.pair_device()
            self.create_activator()
        self.trigger_action('pair')

    def create_activator(self):
        activator = Timer(self.DELAY, self.on_activate)
        activator.daemon = True
        activator.start()
