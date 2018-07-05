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
import atexit
from collections import namedtuple

import functools
from copy import deepcopy
from functools import partial
from os.path import join
from typing import Callable, Union, Any

from mycroft.intent_context import IntentContext
from mycroft.intent_match import IntentMatch
from mycroft.package_cls import Package
from mycroft.plugin.base_plugin import BasePlugin
from mycroft.services.filesystem_service import FilesystemService
from mycroft.util import log
from mycroft.util.misc import safe_run


def compose(functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def __create_intent_decorator(handler_type, intent, intent_engine='file', merge_func=None):
    merge_calls = merge_func.intent_calls if merge_func else []
    entity_calls = merge_func.entity_calls if merge_func else []

    def decorator(func):
        func.intent_calls = sum([
            getattr(func, 'intent_calls', []),
            merge_calls,
            [(func, intent, intent_engine, handler_type)]
        ], [])
        func.entity_calls = entity_calls
        merge_calls.clear()
        func.handler = compose([
            __create_intent_decorator(
                'handler', _intent, _intent_engine, merge_func=func
            )
            for _func, _intent, _intent_engine, _handler_type in func.intent_calls
            if _handler_type == 'prehandler'
        ])
        func.prehandler = compose([
            __create_intent_decorator(
                'prehandler', _intent, _intent_engine, merge_func=func
            )
            for _func, _intent, _intent_engine, _handler_type in func.intent_calls
            if _handler_type == 'handler'
        ])
        return func

    return decorator


def intent_prehandler(intent, intent_engine='file'):
    return __create_intent_decorator('prehandler', intent, intent_engine)


def intent_handler(intent, intent_engine='file'):
    return __create_intent_decorator('handler', intent, intent_engine)


def with_entity(entity, intent_engine='file'):
    def decorator(func):
        func.entity_calls = getattr(func, 'entity_calls', []) + [(entity, intent_engine)]
        return func

    return decorator


ResponseConf = namedtuple('ResponseConf', 'repeat_count wait_time')


class SkillPlugin(BasePlugin):
    """Base class for all Mycroft skills"""

    def __init__(self):
        super().__init__(self.rt)
        self.skill_name = self._attr_name
        self.filesystem = FilesystemService(self.rt, self.rt.paths.skill_dir(self.skill_name))
        self.lang = self.rt.config['lang']

        self.__register_intents()
        self.__scheduled_tasks = []
        atexit.register(self._unload)

    def locale(self, file_name):
        """Returns lines of file in skill's locale/<lang> folder"""
        locale_folder = self.rt.paths.skill_locale(self.skill_name)
        with open(join(locale_folder, file_name), 'r') as f:
            return f.read().strip().split('\n')

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
        if not isinstance(p, Package):
            raise TypeError('Invalid package: {}'.format(p))
        self.rt.query.send_package(deepcopy(p))
        return self.rt.package()

    def package(self, **kwargs):
        """Create an empty package, with the skill attribute prefilled"""
        return self.rt.package(skill=self.skill_name, **kwargs)

    def intent_context(self, intents: list = None, intent_engine: str = 'file'):
        """Create an IntentContext namespaced to the skill"""
        context = IntentContext(self.rt, self.skill_name)
        for intent in intents or []:
            context.register(intent, intent_engine)
        if intents:
            context.compile()
        return context

    def get_response(self, p: Package, intent_context: IntentContext = None,
                     repeat_count=0, ) -> Union[IntentMatch, None]:
        """If intent_context is None, the reply can be anything."""
        orig_p = p
        p = deepcopy(p)
        orig_p.action = None
        p.skip_activation = True
        for i in range(1 + repeat_count):
            self.execute(p)
            response = self.rt.query.get_next_query()
            if response:
                if not intent_context:
                    return IntentMatch(confidence=1.0, query=response)
                matches = intent_context.calc_intents(response)
                match = max(matches, key=lambda x: x.confidence)
                if match.confidence > 0.5:
                    match.intent_id = match.intent_id.split(':')[-1]
                    return match
        return IntentMatch(confidence=0.0, query='', intent_id='')

    def shutdown(self):
        """Called when quitting the program or unloading the skill"""
        pass

    def _unload(self):
        atexit.unregister(self._unload)
        for i in self.__scheduled_tasks:
            self.rt.scheduler.cancel(i)
        safe_run(self.shutdown, label=self.skill_name + ' shutdown')

    def register_entity(self, entity: Any, intent_engine: str = 'file'):
        self.rt.intent.context.register_entity(entity, intent_engine, self.skill_name)

    def register_intent(self, func: Callable, intent: Any,
                        intent_engine='file', handler_type='handler'):
        if hasattr(func, '__get__'):  # Bind to self
            func = func.__get__(self, SkillPlugin)
        self.rt.intent.register(
            intent, self.skill_name, intent_engine,
            func, handler_type
        )

    def __register_intents(self):
        intents = []
        entities = []
        for name in dir(self):
            item = getattr(self, name)
            if callable(item):
                intent_calls = getattr(item, 'intent_calls', None)
                if intent_calls:
                    for params in intent_calls:
                        func, intent, intent_engine, handler_type = params
                        if not intent:
                            log.warning('Skipping empty intent from skill:', self.skill_name)
                            continue
                        intents.append(intent)
                        self.register_intent(func, intent, intent_engine, handler_type)

                entity_calls = getattr(item, 'entity_calls', None)
                if entity_calls:
                    for params in entity_calls:
                        entity, intent_engine = params
                        entities.append(entity)
                        self.register_entity(entity, intent_engine)

        log.debug('Intents for', self.skill_name + ':', intents)
        if entities:
            log.debug('Entities for', self.skill_name + ':', entities)
