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
from typing import Callable, Union

from copy import deepcopy

from mycroft.package_cls import Package
from mycroft.base_plugin import BasePlugin
from mycroft.intent_context import IntentContext
from mycroft.intent_match import IntentMatch
from mycroft.util import log
from mycroft.util.misc import safe_run


def intent_prehandler(intent, intent_engine='padatious'):
    def decorator(func):
        func.handler_type = 'prehandler'
        func.intent_params = intent, intent_engine
        return func

    return decorator


def intent_handler(intent, intent_engine='padatious'):
    def decorator(func):
        func.handler_type = 'handler'
        func.intent_params = intent, intent_engine
        return func

    return decorator


class SkillPlugin(BasePlugin):
    """Base class for all Mycroft skills"""

    def __init__(self):
        super().__init__(self.rt)
        self.skill_name = self._attr_name
        self.config = self.rt.config.load_skill_config(self.rt.paths.skill_conf(self.skill_name))

        self.__register_intents()
        self.__scheduled_tasks = []

    def create_thread(self, target, *args, **kwargs):
        safe_run(target, args=args, kwargs=kwargs, label=self.skill_name + ' thread')

    def schedule_repeating(self, function: Callable, delay: int, name='', args=None, kwargs=None):
        identifier = self.skill_name + ':' + repr(function)
        self.rt.scheduler.repeating(function, delay, name, args, kwargs, identifier)
        self.__scheduled_tasks.append(identifier)

    def schedule_once(self, function: Callable, delay: int, name='', args=None, kwargs=None):
        identifier = self.skill_name + ':' + repr(function)
        self.rt.scheduler.once(function, delay, name, args, kwargs, identifier)
        self.__scheduled_tasks.append(identifier)

    def execute(self, p: Package):
        self.rt.query.send_package(deepcopy(p))

    def get_response(self, p: Package, intent_context: IntentContext = None) -> Union[IntentMatch, None]:
        """If intent_context is None, the reply can be anything."""
        p = deepcopy(p)
        p.skip_activation = True
        self.execute(p)
        while True:
            response = self.rt.query.get_next_query()
            if response:
                if not intent_context:
                    return IntentMatch(confidence=1.0, query=response)
                matches = intent_context.calc_intents(response)
                match = max(matches, key=lambda x: x.confidence)
                if match.confidence > 0.5:
                    return match
            self.execute(p)

    def _unload(self):
        for i in self.__scheduled_tasks:
            self.rt.scheduler.cancel(i)

    def __register_intents(self):
        intents = []
        for name in dir(self):
            item = getattr(self, name)
            if callable(item):
                handler_type = getattr(item, 'handler_type', None)
                if handler_type:
                    intent, intent_engine = getattr(item, 'intent_params')
                    intents.append(intent)
                    self.rt.intent.register(intent, self.skill_name, intent_engine,
                                            item, handler_type)
        log.debug('Intents for', self.skill_name + ':', intents)
