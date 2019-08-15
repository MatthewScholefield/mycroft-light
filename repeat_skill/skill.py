# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
from mycroft_core import MycroftSkill, Package, intent_handler


class RepeatSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.stop_words = self.locale('stop.words.txt')

    @intent_handler('repeat')
    def handle_repeat(self, p: Package):
        p.speech = p.match.matches['text']

    @intent_handler('repeat.after.me')
    def handle_repeat_after_me(self, p: Package):
        response = self.get_response(p).query
        while not any(word in response for word in self.stop_words):
            response = self.get_response(self.package(speech=response)).query
        p.action = None
