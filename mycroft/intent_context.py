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
from typing import Any, List

from mycroft.plugin.group_plugin import GroupPlugin, GroupMeta
from mycroft.intent_match import IntentMatch
from mycroft.intent.intent_plugin import IntentPlugin


class IntentContext(GroupPlugin, metaclass=GroupMeta, base=IntentPlugin, package='mycroft.intent',
                    suffix='_intent'):
    """Used to handle creating both intents and intent engines"""
    _plugin_path = 'intent'

    def __init__(self, rt, skill_name=None):
        GroupPlugin.__init__(self, rt)
        self.skill_name = skill_name
        self.id_to_engine = {}

    @staticmethod
    def create_intent_id(intent: Any, skill_name: str):
        return skill_name + ':' + str(intent)

    def register(self, intent: Any, intent_engine: str = 'file', skill_name: str = None) -> str:
        """
        Register an intent via the corresponding intent engine

        Note: register_intent in the MycroftSkill base class automatically creates a SkillResult
        Args:
            intent: argument used to build intent; can be anything
            intent_engine: name of intent engine to register with. It must be installed
            skill_name: snake_case name without `_skill` suffix

        Returns:
            str: unique intent id associated with this intent

        Raises:
            KeyError: given intent engine does not exist
        """
        skill_name = skill_name or self.skill_name
        if not skill_name:
            raise ValueError('Please provide skill_name in constructor or register()')

        intent_id = self.create_intent_id(intent, skill_name)
        self[intent_engine].register(intent, skill_name, intent_id)
        self.id_to_engine[intent_id] = intent_engine
        return intent_id

    def unregister(self, intent_id: str):
        self[self.id_to_engine[intent_id]].unregister(intent_id)

    def compile(self):
        """Prepare intents for calculation"""
        self.all.compile()

    def calc_intents(self, query: str) -> List[IntentMatch]:
        return sum(filter(bool, self.all.calc_intents(query)), [])
