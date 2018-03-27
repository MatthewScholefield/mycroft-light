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
from typing import Any, Callable, List

from mycroft.group_plugin import GroupPlugin
from mycroft.intent_match import IntentMatch
from mycroft.intents.intent_plugin import IntentPlugin


class IntentContext(GroupPlugin):
    """Used to handle creating both intents and intent engines"""

    def __init__(self, rt):
        GroupPlugin.__init__(self, IntentPlugin, 'mycroft.intents', '_intent')
        self._init_plugins(rt)

        self.skill_intents = {}
        # ------------------------------ Example ------------------------------
        # {
        #    '<skill_name>': {
        #        '<intent_id>',
        #        '<intent_id>',
        #    }
        # }

        self.intent_to_skill = {}

        # Duplicated references for convenience
        self.intent_data = {}
        # ------------------------------ Example ------------------------------
        # {
        #    '<intent_id>': {
        #        'engine': '<engine>',
        #        'prehandler': <prehandler>,  # Optional
        #        'handler': <handler>         # Optional
        #    }
        #    '<intent_id>': {                 # Fallback (engine is nothing)
        #        'engine': '',
        #        'prehandler': <prehandler>,  # Optional
        #        'handler': <handler>         # Optional
        #    }
        # }

    def remove_skill(self, skill_name):
        if skill_name in self.skill_intents:
            for intent_id in self.skill_intents.pop(skill_name):
                data = self.intent_data.pop(intent_id)
                if data['engine']:
                    self[data['engine']].unregister(intent_id)

                if intent_id in self.intent_to_skill:
                    del self.intent_to_skill[intent_id]

    @staticmethod
    def create_intent_id(intent: Any, skill_name: str):
        return skill_name + ':' + str(intent)

    def register(self, intent: Any, skill_name: str,
                 intent_engine: str, handler: Callable, handler_type: str):
        """
        Register an intent via the corresponding intent engine

        Note: register_intent in the MycroftSkill base class automatically creates a SkillResult
        Args:
            intent: argument used to build intent; can be anything
            skill_name: snake_case name without `_skill` suffix
            intent_engine: name of intent engine to register with. It must be installed
            handler: function that calculates the confidence
            handler_type: either 'prehandler' or 'handler'
        """
        intent_id = self.create_intent_id(intent, skill_name)
        if intent_engine:  # Not a fallback
            try:
                self[intent_engine].register(intent, skill_name, intent_id)
            except KeyError:
                raise RuntimeError('Could not find required intent engine: ' + intent_engine)
        data = {
            'engine': intent_engine,
            'id': intent_id,
            handler_type: handler
        }
        self.skill_intents.setdefault(skill_name, set()).add(intent_id)
        self.intent_to_skill[intent_id] = skill_name
        self.intent_data.setdefault(intent_id, {}).update(data)

    def calc_intents(self, query: str) -> List[IntentMatch]:
        return sum(self.all.calc_intents(query), [])
