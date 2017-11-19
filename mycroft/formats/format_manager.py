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

from threading import Thread, Event

from mycroft.formats.client_format import ClientFormat
from mycroft.formats.dialog_format import DialogFormat
from mycroft.formats.faceplate_format import FaceplateFormat
from twiggy import log
from mycroft.util.misc import safe_run


class Empty:
    """Empty class used as placeholder when format not installed"""
    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    def __getitem__(self, item):
        return self


class FormatManager:
    """
    Interface to access various formats. Surrently supported attributes:

    formats.dialog
    formats.client
    formats.faceplate
    """

    def __init__(self, path_manager):
        self.reset_event = Event()
        self.reset_event.set()
        self.formats = {}

        for cls in [ClientFormat, DialogFormat, FaceplateFormat]:
            def add_format():
                obj = cls(path_manager)
                self.formats[obj.attr_name] = obj
            safe_run(add_format)

    def __getattr__(self, item):
        if item in self.formats:
            return self.formats[item]
        else:
            log.warning(item + ' format not available')
            self.formats[item] = Empty()
            return getattr(self, item)

    def generate(self, name, data):
        """Called to send the raw data to the formats to be generated"""
        log.fields(**data).debug('Package data')
        self._reset()
        was_handled = False

        for i in self.formats.values():
            was_handled = i.generate(name, data) or was_handled

        if not was_handled:
            log.warning('No format handled ' + str(name))

    def reset(self):
        if self.reset_event.is_set():
            self._reset()

    def set_reset_event(self, event):
        self.reset_event = event
        Thread(target=self._wait_and_reset, daemon=True).start()

    def _reset(self):
        log.info('Resetting formats...')
        for i in self.formats.values():
            i.reset()

    def _wait_and_reset(self):
        self.reset_event.wait()
        self._reset()
