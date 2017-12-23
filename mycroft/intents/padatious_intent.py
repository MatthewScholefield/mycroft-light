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
import os
from os.path import join

from padatious import IntentContainer

from mycroft.intent_name import IntentName
from mycroft.intents.intent_plugin import IntentPlugin, IntentMatch
from mycroft.util import log


class PadatiousIntent(IntentPlugin):
    """Interface for Padatious intent engine"""

    def __init__(self, rt):
        super().__init__(rt)
        self.container = IntentContainer(join(rt.paths.user_config, 'intent_cache'))

    def try_register_intent(self, *args, **kwargs):
        arg_names = ['skill_name', 'intent_name']
        kwargs.update(dict(zip(arg_names, args)))
        skill_name, intent_name = map(kwargs.get, arg_names)

        if not isinstance(intent_name, str):
            return None
        intent_dir = self.rt.paths.skill_vocab(skill_name)
        file_name = os.path.join(intent_dir, intent_name + '.intent')
        if not os.path.isfile(file_name):
            return None

        name = IntentName(skill_name, intent_name)
        self.container.load_file(str(name), file_name)
        return name

    def try_register_entity(self, skill_name, ent_name):
        if not isinstance(ent_name, str):
            return False
        intent_dir = self.rt.paths.skill_vocab(skill_name)
        file_name = os.path.join(intent_dir, ent_name + '.entity')
        if not os.path.isfile(file_name):
            return False

        self.container.load_entity(ent_name, file_name)
        return True

    def compile(self):
        log.info('Training...')
        self.container.train()
        log.info('Training complete!')

    def calc_intents(self, query):
        matches = []
        for data in self.container.calc_intents(query):
            matches.append(IntentMatch(name=IntentName.from_str(data.name),
                                       confidence=data.conf,
                                       matches=data.matches,
                                       query=query))
        return matches
