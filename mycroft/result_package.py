#
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
#
from mycroft.intent_name import IntentName

class ResultPackage:
    def __init__(self, name=None, data=None, action=None, reset_event=None, callback=lambda x: x, confidence=0.0, prompt=False):
        self.name = IntentName() if name is None else name
        self.data = {} if data is None else data
        self.action = action
        self.callback = callback
        self.confidence = confidence
        self.reset_event = reset_event
        self.prompt = prompt

    def set_name(self, name):
        self.name = name
        if self.action is None:
            self.action = name
        return self
