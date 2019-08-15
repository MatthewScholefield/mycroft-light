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
from copy import deepcopy

from mycroft.util.text import compare
from mycroft_core import MycroftSkill, Package, intent_prehandler


class IntrospectionSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.rt.query.on_response(self.on_response)
        self.last_packages = []

    def on_response(self, p: Package):
        self.last_packages = self.last_packages[-5:] + [deepcopy(p)]

    @intent_prehandler('what.skill.was.that')
    def handle_what_skill(self, p: Package):
        if not self.last_packages:
            return p.add(confidence=0.1)
        if 'phrase' not in p.match:
            last_package = self.last_packages[-1]
        else:
            phrase = p.match['phrase']
            best_match = max(self.last_packages, key=lambda x: compare(phrase, x.match.query))
            best_conf = compare(phrase, best_match.match.query)
            if best_conf < 0.5:
                return p.add(action='no.matching.query', data=dict(phrase=phrase))
            last_package = best_match
        return p.add(data=dict(
            skill=last_package.skill, intent=last_package.match.intent_id.split(':')[0]
        ))
