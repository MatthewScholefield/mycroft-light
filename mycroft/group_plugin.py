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
import pkgutil
import time
from abc import ABCMeta
from functools import wraps
from importlib import import_module
from inspect import isclass
from threading import Thread
from typing import Any, List, Dict, Union

from mycroft.util import log
from mycroft.util.misc import safe_run
from mycroft.util.text import to_camel, to_snake


def run_ordered_parallel(items, get_function, args, kwargs,
                         order=None, daemon=False, label='', warn=False,
                         custom_exception=type(None), custom_handler=None, timeout=None) \
        -> Union[List[Any], Dict[str, Thread]]:
    order = order or []
    if '*' not in order:
        order.append('*')
    if daemon and timeout is None:
        timeout = 0.0
    return_vals = []

    def run_item(item, name):
        return_val = safe_run(get_function(item), args=args, kwargs=kwargs,
                              label=label + ' ' + name, warn=warn,
                              custom_exception=custom_exception, custom_handler=custom_handler)
        return_vals.append(return_val)

    threads = {}
    for name in set(items) - set(order):
        threads[name] = Thread(target=run_item, args=(items[name], name), daemon=daemon)

    for name in order:
        if name == '*':
            for i in threads.values():
                i.start()
            join_threads(threads.values(), timeout)
        elif name in items:
            run_item(items[name], name)
        else:
            log.warning('Plugin from runner load order not found:', name)

    if not daemon:
        return return_vals
    return threads


def join_threads(threads, timeout: float=None) -> bool:
    """Join multiple threads, providing a global timeout"""
    if timeout is None:
        for i in threads:
            i.join()
        return True

    end_time = time.time() + timeout
    for i in threads:
        time_left = end_time - time.time()
        if time_left <= 0:
            return False
        i.join(time_left)
    return True


class GroupRunner(metaclass=ABCMeta):
    def __init__(self, cls, plugins):
        self._plugins = plugins
        self._cls = cls

        for fn_name in filter(lambda x: not x.startswith('_') and callable(getattr(cls, x)),
                              dir(cls)):
            setattr(self, fn_name, self.__make_method(fn_name))

    def __make_method(self, fn_name):
        @wraps(getattr(self._cls, fn_name))
        def method(*args, **kwargs):
            gp_kwargs = GroupPlugin.extract_gp_kwargs(kwargs)
            return run_ordered_parallel(self._plugins, lambda plugin: getattr(plugin, fn_name),
                                        args=args, kwargs=kwargs, label='Running all.' + fn_name,
                                        **gp_kwargs)

        return method

    def __getattribute__(self, item) -> list:
        try:
            return super().__getattribute__(item)
        except AttributeError:
            raise AttributeError(
                "'" + self._cls.__name__ + "' base class has no method '" + item + "'")


class Empty:
    """Empty class used as placeholder when format not installed"""

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False

    def __getitem__(self, item):
        return self


class GroupPlugin(metaclass=ABCMeta):
    def __init__(self, base_cls, package, suffix):
        self._plugins = {}
        self._classes = {}
        self._suffix = ''
        self._base_cls = None
        self._error_label = 'Loading plugin'
        self.all = None  # type: GroupRunner

        self._load_plugins(base_cls, package, suffix)

    @staticmethod
    def extract_gp_kwargs(kwargs):
        gp_kwargs = {}
        for name in list(kwargs):
            if name.startswith('gp_'):
                gp_kwargs[name.replace('gp_', '')] = kwargs.pop(name)
        return gp_kwargs

    def _load_classes(self, package, suffix):
        classes = {}
        folder = list(import_module(package).__path__)[0]
        for loader, mod_name, is_pkg in pkgutil.walk_packages([folder]):
            if not mod_name.endswith(suffix):
                continue

            log.debug('Loading', mod_name + '...')

            try:
                module = loader.find_module(mod_name).load_module(mod_name)
            except Exception:
                log.exception('Loading', mod_name)
                continue
            cls_name = to_camel(mod_name)
            mod_cls = getattr(module, cls_name, '')
            if not isclass(mod_cls):
                log.warning('Could not find', cls_name, 'in', mod_name)
                continue

            try:
                plugin_path = object.__getattribute__(self, '_plugin_path') + '.'
            except AttributeError:
                plugin_path = ''

            mod_cls._attr_name = self._make_name(mod_cls)
            mod_cls._plugin_path = plugin_path + mod_cls._attr_name

            classes[mod_cls._attr_name] = mod_cls
        return classes

    def _load_plugins(self, base_cls, package, suffix):
        self._plugins = {}
        self._suffix = suffix
        self._base_cls = base_cls
        self.all = None
        self._classes = self._load_classes(package, suffix)

    def _make_name(self, cls):
        return to_snake(cls.__name__).replace(self._suffix, '')

    def _init_plugins(self, *args, **kwargs) -> Dict[str, Thread]:
        """
        Call __init__ of all plugins. *args and **kwargs match the base plugin's __init__
        Args:
            gp_order (list): List of attribute names in load order.
                    Other attributes will be loaded after
        Returns:
            Threads of plugin init methods
        """

        def get_function(cls):
            def function(*args, **kwargs):
                self._plugins[self._make_name(cls)] = cls(*args, **kwargs)

            return function

        gp_kwargs = GroupPlugin.extract_gp_kwargs(kwargs)
        threads = run_ordered_parallel(self._classes, get_function,
                                       args=args, kwargs=kwargs, label=self._error_label,
                                       custom_exception=NotImplementedError,
                                       custom_handler=lambda e, l:
                                       log.info(l + ': Skipping disabled plugin'),
                                       **gp_kwargs)
        self.all = GroupRunner(self._base_cls, self._plugins)
        return threads

    def __repr__(self):
        return self._base_cls.__name__ + ': ' + repr(self._plugins)

    def __str__(self):
        return self._base_cls.__name__ + ': ' + str(list(self._plugins.keys()))

    def __getattribute__(self, item) -> Any:
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            pass

        if 'all' not in self.__dict__:
            raise RuntimeError('Please call GroupPlugin.__init__ first')

        if item not in object.__getattribute__(self, '_plugins'):
            log.warning(item, 'plugin does not exist.', stack_offset=1)
            self._plugins[item] = Empty()
        return object.__getattribute__(self, '_plugins')[item]

    def __getitem__(self, item) -> Any:
        return self._plugins[item]

    def __iter__(self):
        return iter(self._plugins)
