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

from mycroft_core import MycroftSkill, Package, intent_handler
from mycroft.api import DeviceApi


class PairingSkill(MycroftSkill):
    DELAY = 30
    EXPIRATION = 20 * 60 * 60  # 20 hours
    WORDS = {
        'A': 'Apple', 'B': 'Bravo',
        'C': 'Charlie', 'D': 'Delta',
        'E': 'Echo', 'F': 'Fox trot',
        'G': 'Golf', 'H': 'Hotel',
        'I': 'India', 'J': 'Juliet',
        'K': 'Kilogram', 'L': 'London',
        'M': 'Mike', 'N': 'November',
        'O': 'Oscar', 'P': 'Paul',
        'Q': 'Quebec', 'R': 'Romeo',
        'S': 'Sierra', 'T': 'Tango',
        'U': 'Uniform', 'V': 'Victor',
        'W': 'Whiskey', 'X': 'X-Ray',
        'Y': 'Yankee', 'Z': 'Zebra'
    }

    def __init__(self):
        super().__init__()
        self.activator = None

        if not self.rt.identity:
            raise NotImplementedError('Server Disabled')

        self.api = DeviceApi(self.rt)
        self.data = None
        self.expire_time = None
        self.state = str(uuid4())
        self.check_paired()

        self.confirm_context = self.intent_context(['yes', 'no'])

    def check_paired(self):
        if not self.rt.device_info:
            package = self.pair_device(self.package())
            self.execute(package)

    def spell_code(self, code: str) -> str:
        return ', '.join(
            c if c in '0123456789' else
            '{} as in {}'.format(c, self.WORDS[c])
            for c in code
        )

    @intent_handler('pair.device')
    def pair_device(self, p: Package):
        if not self.rt.identity:
            return p.add(action='server.disabled', confidence=0.6)

        if self.rt.device_info:
            return p.add(action='already.paired', confidence=0.6)

        if not self.data or self.expire_time < time.time():
            self.create_new_code()
            if not self.data:
                return p.add(action='could.not.fetch.pairing')

        self.create_activator()

        code = self.data['code']

        return p.add(
            action='pair', confidence=0.85,
            data=dict(code=code, spelt_code=self.spell_code(code)),
        )

    @intent_handler('stop.pairing')
    def stop_pairing(self, p: Package):
        if self.activator:
            self.activator.cancel()
        else:
            p.action = 'not.pairing'

    @intent_handler('unpair.device')
    def unpair_device(self, p: Package):
        if not self.rt.identity:
            return p.add(action='server.disabled', confidence=0.5,
                         data={'status': 'down'})

        if not self.rt.device_info:
            return p.add(action='already.unpaired')

        answer = self.get_response(p.add(action='confirm'), self.confirm_context).intent_id
        if answer == 'yes':
            self.rt.device_info.clear()
            self.rt.identity.assign(dict(uuid='', access='', refresh='', expires_at=0))
            self.execute(self.pair_device(p))
            return p.add(action='unpaired')
        else:
            return p.add(action='canceled')

    def create_new_code(self):
        self.expire_time = time.time() + self.EXPIRATION
        self.data = self.api.get_code(self.state)

    def check_activate(self):
        token = self.data.get('token')
        try:
            # wait for a signal from the backend that pairing is complete
            login = self.api.activate(self.state, token)
        except ConnectionError:
            self.execute(self.pair_device(self.package()))
            return

        self.rt.identity.register(login)
        self.rt.device_info.reload()
        self.execute(self.package(action='pair.complete'))

    def create_activator(self):
        self.activator = Timer(self.DELAY, self.check_activate)
        self.activator.daemon = True
        self.activator.start()

    def shutdown(self):
        if self.activator:
            self.activator.cancel()
