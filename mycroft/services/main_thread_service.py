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

from mycroft.services.service_plugin import ServicePlugin


class MainThreadService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.quit_event = Event()

    def __bool__(self):
        return not self.quit_event.is_set()

    def quit(self):
        self.quit_event.set()

    def wait(self):
        self.quit_event.wait()
