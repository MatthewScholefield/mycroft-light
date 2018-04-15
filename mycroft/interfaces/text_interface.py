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
from mycroft.util import log


class TextInterface(InterfacePlugin):
    """Interact with Mycroft via a terminal"""

    def __init__(self, rt):
        super().__init__(rt)
        self.response_event = Event()
        self.response_event.set()
        self.prompt = self.config['prompt']

    def owns_response(self):
        return not self.response_event.is_set()

    def run(self):
        print(self.prompt, end='')
        try:
            while self.rt.main_thread:
                query = input()
                self.response_event.clear()
                self.send_query(query)
                self.response_event.wait()
        except (EOFError, KeyboardInterrupt):
            self.rt.main_thread.quit()

    def on_query(self, query):
        if query and not self.owns_response():
            print(query)

    def on_response(self, package):
        if not self.owns_response():
            print()
        print()
        print("    " + package.text)
        print()
        print(self.prompt, end='')
        self.response_event.set()

    def on_exit(self):
        print()
