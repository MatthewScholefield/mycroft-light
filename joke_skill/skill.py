# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
import pyjokes
import re

from mycroft.skill_plugin import with_entity
from mycroft_core import MycroftSkill, Package, intent_handler


def find_entity_line(word, lines):
    """Return line number with word. Starts at 1. Returns 0 if not found"""
    for i, line in enumerate(lines, 1):
        if word in re.findall(r'\w+', line):
            return i
    return 0


class JokeSkill(MycroftSkill):
    joke_types = {
        1: 'neutral',
        2: 'adult',
        3: 'chuck',
        4: 'any'
    }

    @with_entity('joke_type')
    @intent_handler('joke')
    def joke(self, p: Package):
        joke_type_word = p.match.get('joke_type')
        joke_id = find_entity_line(joke_type_word, self.locale('joke_type.entity'))
        category = self.joke_types.get(joke_id, 'neutral')
        p.speech = pyjokes.get_joke(language=self.lang.split('-')[0],
                                    category=category)
