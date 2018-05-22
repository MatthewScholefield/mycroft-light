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
from contextlib import suppress
from inspect import signature
from math import sqrt
from typing import Callable, List, Union, Any

from mycroft.intent_context import IntentContext
from mycroft.intent_match import IntentMatch, MissingIntentMatch
from mycroft.package_cls import Package
from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log
from mycroft.util.parallel import run_parallel


class IntentService(ServicePlugin):
    """Used to handle creating both intents and intent engines"""
    _package_struct = {
        'data': dict,
        'skill': str,
        'lang': str,
        'match': IntentMatch,
        'action': str,
        'confidence': float
    }

    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)

        self.rt.package.data = {}
        self.rt.package.skill = ''
        self.rt.package.lang = self.rt.config['lang']
        self.rt.package.match = IntentMatch()
        self.rt.package.action = ''
        self.rt.package.confidence = 0.75

        self.context = IntentContext(self.rt)

        self.skill_intents = {}
        # ------------------------------ Example ------------------------------
        # {
        #    '<skill_name>': {
        #        '<intent_id>',
        #        '<intent_id>',
        #    }
        # }

        self.intent_to_skill = {}
        self.fallback_intents = set()
        self.intent_data = {}
        # ------------------------------ Example ------------------------------
        # {
        #    '<intent_id>': {
        #        'prehandler': <prehandler>,  # Optional
        #        'handler': <handler>         # Optional
        #    }
        #    '<intent_id>': {
        #        'prehandler': <prehandler>,  # Optional
        #        'handler': <handler>         # Optional
        #    }
        # }

    def remove_skill(self, skill_name):
        if skill_name in self.skill_intents:
            for intent_id in self.skill_intents.pop(skill_name):
                del self.intent_data[intent_id]

                if intent_id in self.intent_to_skill:
                    del self.intent_to_skill[intent_id]

                if intent_id in self.fallback_intents:
                    self.fallback_intents.remove(intent_id)
                else:
                    self.context.unregister(intent_id)

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
        if not intent_engine:  # A fallback
            intent_id = IntentContext.create_intent_id('fallback', skill_name)
            self.fallback_intents.add(intent_id)
        else:
            try:
                intent_id = self.context.register(intent, intent_engine, skill_name)
            except KeyError:
                raise RuntimeError('Could not find required intent engine: ' + intent_engine)
        data = {
            handler_type: handler
        }
        self.skill_intents.setdefault(skill_name, set()).add(intent_id)
        self.intent_to_skill[intent_id] = skill_name
        self.intent_data.setdefault(intent_id, {}).update(data)

    @staticmethod
    def default_prehandler(p: Package):
        return p

    @staticmethod
    def default_handler(p: Package):
        return p

    def calc_package(self, query: str) -> Package:
        """
        Find the best intent and run the handler to find the result

        Args:
            query: input sentence
        Returns:
            package: object containing display data from skill
        """
        query = query.strip().lower()

        matches = self.context.calc_intents(query)
        matches = [i for i in matches if i.confidence > 0.5]

        packages = self._run_prehandlers(matches)
        result_package = self._try_run_packages([i for i in packages if i.confidence > 0.5])
        if result_package:
            return result_package
        log.info('Falling back.')

        matches = [
            IntentMatch(intent_id, confidence=None, query=query)
            for intent_id in self.fallback_intents
        ]

        packages = self._run_prehandlers(matches)
        result_package = self._try_run_packages(list(packages))
        if result_package:
            return result_package
        log.info('All fallbacks failed.')

        return self.rt.package()

    @staticmethod
    def _run_handler(handler: Callable, p: Package) -> Package:
        try:
            if len(signature(handler).parameters) == 0:
                return handler() or p
            else:
                return handler(p) or p
        except MissingIntentMatch:
            p.confidence = 0.0
            return p

    def _run_prehandlers(self, matches: List[IntentMatch]) -> List[Package]:
        """Iterate through matches, executing prehandlers"""
        package_generators = []
        for match in matches:
            def callback(match=match):
                data = self.intent_data[match.intent_id]
                prehandler = data.get('prehandler', self.default_prehandler)
                package = self.rt.package(match=match)
                package.skill = self.intent_to_skill[match.intent_id]
                return self._run_handler(prehandler, package)

            package_generators.append(callback)

        for package in run_parallel(package_generators, filter_none=True, label='prehandler'):
            match = package.match

            log.info(str(match.intent_id) + ':', str(match.confidence))
            log.debug('\tConfidence:', package.confidence)

            if match.confidence is not None:
                package.confidence = sqrt(package.confidence * match.confidence)
            yield package

    def _try_run_packages(self, packages: List[Package]) -> Union[Package, None]:
        """Iterates through packages, executing handlers until one succeeds"""
        while len(packages) > 0:
            package = max(packages, key=lambda x: x.confidence)
            intent_id = package.match.intent_id
            del packages[packages.index(package)]
            log.info('Selected intent', intent_id, package.confidence)
            try:
                handler = self.intent_data[intent_id].get('handler', self.default_handler)
                return self._run_handler(handler, package)
            except Exception:
                log.exception(intent_id, 'callback')
        return None
