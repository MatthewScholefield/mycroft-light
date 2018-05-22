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
from os.path import join
from typing import Any

from padatious import IntentContainer

from mycroft.intent.intent_plugin import IntentPlugin, IntentMatch
from mycroft.util import log


class PadatiousFileIntent(IntentPlugin):
    """Interface for Padatious intent engine"""

    def __init__(self, rt):
        super().__init__(rt)
        self.container = IntentContainer(join(rt.paths.user_config, 'intent_cache'))

    def register(self, intent: Any, skill_name: str, intent_id: str):
        file_name = join(self.rt.paths.skill_locale(skill_name), intent + '.intent')
        self.container.load_intent(name=intent_id, file_name=file_name)

    def register_entity(self, entity: Any, entity_id: str, skill_name: str):
        file_name = join(self.rt.paths.skill_locale(skill_name), entity + '.intent')
        self.container.load_intent(name=entity_id, file_name=file_name)

    def unregister(self, intent_id: str):
        self.container.remove_intent(intent_id)

    def unregister_entity(self, entity_id: str):
        self.container.remove_entity(entity_id)

    def compile(self):
        log.info('Training...')
        self.container.train()
        log.info('Training complete!')

    def calc_intents(self, query):
        return [
            IntentMatch(intent_id=data.name, confidence=data.conf,
                        matches=data.matches, query=query)
            for data in self.container.calc_intents(query)
        ]
