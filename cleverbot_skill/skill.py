#
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
#
from cleverwrap.cleverwrap import CleverWrap

from mycroft import MycroftSkill


class CleverbotSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        key = self.config['api_key']
        if key is None:
            raise ValueError
        self.cw = CleverWrap(key)
        self.register_fallback(self.fallback)

    def fallback(self, query):
        if len(query) == 0:
            return 0.0
        self.set_callback(lambda: self.add_result('response', self.cw.say(query)))
        return 0.6
