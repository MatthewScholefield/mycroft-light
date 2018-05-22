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
from threading import Event

from mycroft.interfaces.interface_plugin import InterfacePlugin
from mycroft.interfaces.tts.tts_plugin import TtsPlugin
from mycroft.plugin.option_plugin import OptionMeta, OptionPlugin


class TtsInterface(
    InterfacePlugin, OptionPlugin, metaclass=OptionMeta, base=TtsPlugin,
    package='mycroft.interfaces.tts', suffix='_tts', default='mimic'
):
    """Speak outputs"""
    def __init__(self, rt):
        InterfacePlugin.__init__(self, rt)
        OptionPlugin.__init__(self, rt, __module__=self.config['module'])
        self.event = Event()

    def on_response(self, package):
        self.read(package.speech)
        self.event.set()
        self.event.clear()

    def wait(self):
        self.event.wait()
