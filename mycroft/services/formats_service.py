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
import json
from threading import Thread, Event

from mycroft.formats.format_plugin import FormatPlugin
from mycroft.group_plugin import GroupPlugin
from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log


class FormatsService(ServicePlugin, GroupPlugin):
    """
    Interface to access various formats. Currently supported attributes:

    rt.formats.dialog
    rt.formats.client
    rt.formats.faceplate
    """

    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        GroupPlugin.__init__(self, FormatPlugin, 'mycroft.formats', '_format')
        self.init_plugins(rt)

        self.reset_event = Event()
        self.reset_event.set()

    def generate(self, name, data):
        """Called to send the raw data to the formats to be generated"""
        log.debug('Package data: \n' + json.dumps(data, indent=4))
        self.all.reset()

        was_handled = any(self.all.generate(name, data, gp_warn=False))

        if not was_handled:
            log.warning('No format handled ' + str(name))

    def reset(self):
        if self.reset_event.is_set():
            self.all.reset()

    def set_reset_event(self, event):
        self.reset_event = event
        Thread(target=self._wait_and_reset, daemon=True).start()

    def _wait_and_reset(self):
        self.reset_event.wait()
        self.all.reset()
