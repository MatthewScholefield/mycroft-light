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

from mycroft.engines.intent_engine import IntentMatch
from mycroft.engines.padatious_engine import PadatiousEngine
from mycroft.intent_name import IntentName
from mycroft.result_package import ResultPackage
from twiggy import log

engine_classes = [PadatiousEngine]


class IntentManager:
    """Used to handle creating both intents and intent engines"""

    def __init__(self, path_manager):
        self.engines = [i(path_manager) for i in engine_classes]
        self.handlers_s = {}  # Example: { 'SkillName:intent.name': [intent_name_handler, alias_name_handler] }
        self.fallbacks = []

    def _add_handler(self, str_name, handler):
        if str_name in self.handlers_s:
            self.handlers_s[str_name].append(handler)
        else:
            self.handlers_s[str_name] = [handler]
        return

    def remove_skill(self, skill_name):
        for key in list(self.handlers_s):
            if key.split(':')[0] == skill_name:
                del self.handlers_s[key]

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
        for i in self.engines:
            intent_name = i.try_register_intent(skill_name, intent)
            if intent_name is not None:
                self._add_handler(str(intent_name), lambda x: calc_conf_fn(x).set_name(intent_name))
                return
        print("Failed to register intent for " + str(IntentName(skill_name, str(intent))))

    def register_entity(self, skill_name, entity):
        for i in self.engines:
            if i.try_register_entity(skill_name, entity):
                return
        print("Failed to register entity for " + str(IntentName(skill_name, entity)))

    def create_alias(self, skill_name, alias_intent, intent):
        """
        Register an intent that uses the same handler as another intent
        Args:
            skill_name (str):
            alias_intent (obj): argument used to build intent; can be anything
            intent (str): Name of intent to copy from
        """
        for i in self.engines:
            intent_name = i.try_register_intent(skill_name, alias_intent)
            if intent_name is not None:
                for handler in self.handlers_s[str(IntentName(skill_name, intent))]:
                    self._add_handler(str(intent_name), handler)
                return
        print("Failed to register alias for " + str(IntentName(skill_name, str(intent))))

    def register_fallback(self, skill_name, calc_conf_fn):
        """
        Register a function to be called as a general knowledge fallback

        Args:
            calc_conf_fn (obj): function that receives query and returns a SkillResult
                        note: register_fallback in the MycroftSkill base class automatically generates a SkillResult
        """
        intent_name = IntentName(skill_name, 'fallback')
        self.fallbacks.append(lambda x: calc_conf_fn(x).set_name(intent_name))

    def on_intents_loaded(self):
        for i in self.engines:
            i.on_intents_loaded()

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

        for i in self.engines:
            merge_matches(i.calc_intents(query))

        to_test = [match for match in intent_matches if match.confidence > 0.5]

        best_package = ResultPackage()
        for match in to_test:
            log.info(str(match.name) + ': ' + str(match.confidence))
            for handler in self.handlers_s[str(match.name)]:
                package = handler(match)
                log.debug('\tConfidence: ' + str(package.confidence))
                package.confidence = sqrt(package.confidence * match.confidence)
                if package.confidence > best_package.confidence:
                    best_package = package

        if best_package.confidence > 0.5:
            log.info('Selected intent ' + str(best_package.name))
            try:
                return best_package.callback(best_package)
            except:
                log.trace('error').info(str(best_package.name) + ' callback')

        best_match = max(intent_matches, key=lambda x: x.confidence)
        log.info('Falling back. Too low: ' + str(best_match.name) + ' ' + str(best_match.confidence))

        best_package = ResultPackage()
        for handler in self.fallbacks:
            package = handler(query)
            log.debug('\tConfidence: ' + str(package.confidence))
            if package.confidence > best_package.confidence:
                best_package = package

        try:
            return best_package.callback(best_package)
        except:
            log.trace('error').info(str(best_package.name) + ' callback')
            return ResultPackage(action=IntentName())
