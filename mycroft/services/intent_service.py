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
from typing import Callable, List, Union

from mycroft.intent_context import IntentContext
from mycroft.intent_match import IntentMatch
from mycroft.package_cls import Package
from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log
from mycroft.util.misc import run_parallel


class IntentService(ServicePlugin, IntentContext):
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
        IntentContext.__init__(self, rt)

        self.rt.package.data = {}
        self.rt.package.skill = ''
        self.rt.package.lang = self.rt.config['lang']
        self.rt.package.match = IntentMatch()
        self.rt.package.action = ''
        self.rt.package.confidence = 0.0

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

        matches = self.calc_intents(query)
        matches = [i for i in matches if i.confidence > 0.5]

        packages = self._run_prehandlers(matches)
        result_package = self._try_run_packages([i for i in packages if i.confidence > 0.5])
        if result_package:
            return result_package
        log.info('Falling back.')

        matches = [
            IntentMatch(intent_id, confidence=None)
            for intent_id, data in self.intent_data.items()
            if not data['engine']
        ]

        packages = self._run_prehandlers(matches)
        result_package = self._try_run_packages(list(packages))
        if result_package:
            return result_package
        log.info('All fallbacks failed.')

        return self.rt.package.new()

    @staticmethod
    def _run_handler(handler: Callable, p: Package) -> Package:
        try:
            return handler(p) or p
        except TypeError:
            pass
        return handler() or p

    def _run_prehandlers(self, matches: List[IntentMatch]) -> List[Package]:
        """Iterate through matches, executing prehandlers"""
        package_generators = []
        for match in matches:
            def callback(match=match):
                data = self.intent_data[match.intent_id]
                prehandler = data.get('prehandler', self.default_prehandler)
                package = self.rt.package.new()
                package.confidence = 0.75
                package.match = match
                package.skill = self.intent_to_skill[match.intent_id]
                return self._run_handler(prehandler, package)

            package_generators.append(callback)

        for package in run_parallel(package_generators, filter_none=True):
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
