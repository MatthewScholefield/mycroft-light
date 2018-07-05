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
from padaos import IntentContainer
from typing import Any

from mycroft.intent.intent_plugin import IntentPlugin, IntentMatch, DynamicEntity, DynamicIntent
from mycroft.util import log


class PadaosFileIntent(IntentPlugin):
    """Interface for Padatious intent engine"""

    def __init__(self, rt):
        super().__init__(rt)
        self.container = IntentContainer()

    def _read_file(self, file_name):
        with open(file_name) as f:
            return [i.strip() for i in f.readlines() if i.strip()]

    def register(self, intent: Any, skill_name: str, intent_id: str):
        if not isinstance(intent, DynamicIntent):
            file_name = join(self.rt.paths.skill_locale(skill_name), intent + '.intent')
            intent = DynamicIntent(intent, self._read_file(file_name))
        self.container.add_intent(intent_id, intent.data)

    def register_entity(self, entity: Any, skill_name: str, entity_id: str):
        if not isinstance(entity, DynamicEntity):
            file_name = join(self.rt.paths.skill_locale(skill_name), entity + '.entity')
            entity = DynamicEntity(entity, self._read_file(file_name))
        self.container.add_entity(entity_id, entity.data)

    def unregister(self, intent_id: str):
        self.container.remove_intent(intent_id)

    def unregister_entity(self, entity_id: str):
        self.container.remove_entity(entity_id)

    def compile(self):
        self.container.compile()

    def calc_intents(self, query):
        return [
            IntentMatch(intent_id=match['name'], confidence=1.0,
                        matches=match['entities'], query=query)
            for match in self.container.calc_intents(query)
        ]
