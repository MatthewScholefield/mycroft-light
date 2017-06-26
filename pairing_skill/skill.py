# Copyright 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

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
        self.register_intent('pair', self.pair_device)
        self.pair_device()

    def pair_device(self, intent_data=None):
        if is_paired():
            self.add_action('pair.complete')
        elif self.data and self.last_request < time.time():
            self.add_result('code', self.data.get("code"))
        else:
            self.last_request = time.time() + self.EXPIRATION
            self.data = self.api.get_code(self.state)
            self.add_result('code', self.data.get("code"))
            self._create_activator()

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
                self.pair_device()
            else:
                self._create_activator()

    def _create_activator(self):
        activator = Timer(self.DELAY, self.on_activate)
        activator.daemon = True
        activator.start()
