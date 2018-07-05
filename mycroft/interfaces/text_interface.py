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
import sys

from io import StringIO
from threading import Event
from typing import Callable

from mycroft.interfaces.interface_plugin import InterfacePlugin
from mycroft.util import log


class StreamHandler(StringIO):
    def __init__(self, handler: Callable):
        super().__init__()
        self.buffer = ''
        self.handler = handler

    def flush(self):
        self.buffer = self.buffer.strip()
        if self.buffer:
            self.handler(self.buffer)
            self.buffer = ''

    def write(self, text):
        self.buffer += text
        if '\n' in text:
            self.flush()


class TextInterface(InterfacePlugin):
    """Interact with Mycroft via a terminal"""
    _config = {'prompt': 'Input: '}

    def __init__(self, rt):
        super().__init__(rt)
        sys.stdout = StreamHandler(lambda x: log.info(x, stack_offset=3))
        sys.stderr = StreamHandler(lambda x: log.error(x, stack_offset=3))
        self.response_event = Event()
        self.response_event.set()
        self.prompt = self.config['prompt']

    def owns_response(self):
        return not self.response_event.is_set()

    def run(self):
        self.print(self.prompt, end='')
        try:
            while self.rt.main_thread:
                query = input()
                self.response_event.clear()
                self.send_query(query)
                self.response_event.wait()
        except (EOFError, KeyboardInterrupt):
            self.rt.main_thread.quit()

    def on_query(self, query):
        if not self.owns_response():
            self.print(query)
            self.response_event.clear()

    def print(self, *args, **kwargs):
        print(*args, file=sys.__stdout__, flush=True, **kwargs)

    def on_response(self, package):
        if not self.owns_response():
            self.print()
        if package.text:
            self.print()
            self.print("    " + package.text)
            self.print()
        self.print(self.prompt, end='')
        self.response_event.set()

    def on_exit(self):
        self.print()
