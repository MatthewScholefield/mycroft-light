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

from math import sqrt

from mycroft.group_plugin import GroupPlugin
from mycroft.intent_name import IntentName
from mycroft.intents.intent_plugin import IntentPlugin, IntentMatch
from mycroft.managers.manager_plugin import ManagerPlugin
from mycroft.result_package import ResultPackage
from mycroft.util import log
from mycroft.util.misc import run_parallel


class IntentManager(ManagerPlugin, GroupPlugin):
    """Used to handle creating both intents and intent engines"""

    def __init__(self, rt):
        ManagerPlugin.__init__(self, rt)
        GroupPlugin.__init__(self, IntentPlugin, 'mycroft.intents', '_intent')
        self.init_plugins(rt)
        self.handlers_s = {}  # Example: { 'skill_name:intent.name': [intent_name_handler, alias_name_handler] }
        self.fallbacks_s = {}

    def _add_handler(self, dest, str_name, handler):
        if str_name in dest:
            dest[str_name].append(handler)
        else:
            dest[str_name] = [handler]
        return

    def remove_skill(self, skill_name):
        for key in list(self.handlers_s):
            if key.split(':')[0] == skill_name:
                del self.handlers_s[key]

        for key in list(self.fallbacks_s):
            if key == skill_name:
                del self.fallbacks_s[key]

    def register_intent(self, skill_name, intent, calc_conf_fn):
        """
        Register an intent via the corresponding intent engine
        It tries passing the arguments to each engine until one can interpret it correctly

        Note: register_intent in the MycroftSkill base class automatically creates a SkillResult
        Args:
            skill_name (str):
            intent (obj): argument used to build intent; can be anything
            calc_conf_fn (func): function that calculates the confidence
        """
        for i in self._plugins.values():
            intent_name = i.try_register_intent(skill_name, intent)
            if intent_name is not None:
                self._add_handler(self.handlers_s, str(intent_name),
                                  lambda x: calc_conf_fn(x).set_name(intent_name))
                return
        log.warning("Failed to register intent for " + str(IntentName(skill_name, str(intent))), stack_offset=2)

    def register_entity(self, skill_name, entity):
        for i in self._plugins.values():
            if i.try_register_entity(skill_name, entity):
                return
        log.warning("Failed to register entity for " + str(IntentName(skill_name, entity)), stack_offset=2)

    def create_alias(self, skill_name, alias_intent, intent):
        """
        Register an intent that uses the same handler as another intent
        Args:
            skill_name (str):
            alias_intent (obj): argument used to build intent; can be anything
            intent (str): Name of intent to copy from
        """
        for i in self._plugins.values():
            intent_name = i.try_register_intent(skill_name, alias_intent)
            if intent_name is not None:
                for handler in self.handlers_s[str(IntentName(skill_name, intent))]:
                    self._add_handler(self.handlers_s, str(intent_name), handler)
                return
        log.warning("Failed to register alias for " + str(IntentName(skill_name, str(intent))), stack_offset=2)

    def register_fallback(self, skill_name, calc_conf_fn):
        """
        Register a function to be called as a general knowledge fallback

        Args:
            calc_conf_fn (obj): function that receives query and returns a SkillResult
                        note: register_fallback in the MycroftSkill base class automatically generates a SkillResult
        """
        intent_name = IntentName(skill_name, 'fallback')
        self._add_handler(self.fallbacks_s, skill_name,
                          lambda x: calc_conf_fn(x).set_name(intent_name))

    def calc_result(self, query):
        """
        Find the best intent and run the handler to find the result

        Args:
            query (str): input sentence
        Returns:
            result (SkillResult): object containing data from skill
        """

        query = query.strip().lower()

        # A list of IntentMatch objects
        intent_matches = []

        def merge_matches(new_matches):
            """Merge new matches with old ones, keeping ones with higher confidences"""
            for new_match in new_matches:
                found_match = False
                for i in range(len(intent_matches)):
                    if intent_matches[i].name == new_match.name:
                        intent_matches[i] = IntentMatch.merge(intent_matches[i], new_match)
                        found_match = True
                        break
                if not found_match:
                    intent_matches.append(new_match)

        for i in self._plugins.values():
            merge_matches(i.calc_intents(query))

        to_test = [match for match in intent_matches if match.confidence > 0.5]

        functions = []
        for match in to_test:
            for handler in self.handlers_s[str(match.name)]:
                functions.append(lambda m=match, h=handler: (m, h(m)))
        packages = run_parallel(functions)

        best_package = ResultPackage()
        for match, package in packages:
            log.info(str(match.name) + ':', str(match.confidence))
            log.debug('\tConfidence:', package.confidence)
            package.confidence = sqrt(package.confidence * match.confidence)
            if package.confidence > best_package.confidence:
                best_package = package

        if best_package.confidence > 0.5:
            log.info('Selected intent', best_package.name, best_package.confidence)
            try:
                return best_package.callback(best_package)
            except:
                log.exception(best_package.name, 'callback')
        log.info('Falling back. Too low:', best_package.name, best_package.confidence)

        functions = []
        for name, handlers in self.fallbacks_s.items():
            for handler in handlers:
                functions.append(lambda name=name, handler=handler: (name, handler(query)))
        packages = run_parallel(functions)

        best_package = ResultPackage()
        for name, package in packages:
            log.debug(name + ':', package.confidence)
            if package.confidence > best_package.confidence:
                best_package = package

        try:
            return best_package.callback(best_package)
        except:
            log.exception(best_package.name, 'callback')
            return ResultPackage(action=IntentName())
