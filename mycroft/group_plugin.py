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
from abc import ABCMeta
from importlib import import_module
from inspect import isclass
from threading import Thread

from mycroft.util import log
from mycroft.util.misc import safe_run
from mycroft.util.text import to_camel, to_snake


def run_ordered_parallel(items, get_function, *args, gp_order=None, gp_daemon=False, gp_label='',
                         gp_warn=False, **kwargs):
    return_vals = []

    def run_item(item, name):
        return_val = safe_run(get_function(item), label=gp_label + ' ' + name, args=args,
                              kwargs=kwargs, warn=gp_warn)
        return_vals.append(return_val)

    remaining = list(items)
    for name in gp_order or []:
        if name in items:
            run_item(items[name], name)
            remaining.remove(name)
        else:
            log.warning('Plugin from runner load order not found:', name)

    threads = []
    for name in remaining:
        threads.append(Thread(target=run_item, args=(items[name], name), daemon=gp_daemon))

    for i in threads:
        i.start()

    if not gp_daemon:
        for i in threads:
            i.join()
        return return_vals
    return None


class GroupRunner(metaclass=ABCMeta):
    def __init__(self, cls, plugins):
        self._plugins = plugins
        self._cls = cls

        for fn_name in filter(lambda x: not x.startswith('_') and callable(getattr(cls, x)),
                              dir(cls)):
            setattr(self, fn_name, self.__make_method(fn_name))

    def __make_method(self, fn_name):
        return lambda *args, **kwargs: run_ordered_parallel(self._plugins,
                                                            lambda plugin: getattr(plugin, fn_name),
                                                            *args,
                                                            gp_label='Running all.' + fn_name,
                                                            **kwargs)

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

    def _load_classes(self, package, suffix):
        classes = {}
        folder = list(import_module(package).__path__)[0]
        for loader, mod_name, is_pkg in pkgutil.walk_packages([folder]):
            if not mod_name.endswith(suffix):
                continue
            try:
                module = loader.find_module(mod_name).load_module(mod_name)
            except:
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

    def _init_plugins(self, *args, **kwargs):
        """
        Args:
            gp_order (list): List of attribute names in load order.
                    Other attributes will be loaded after
        """

        def get_function(cls):
            def function(*args, **kwargs):
                self._plugins[self._make_name(cls)] = cls(*args, **kwargs)

            return function

        run_ordered_parallel(self._classes, get_function, *args, gp_label=self._error_label,
                             **kwargs)
        self.all = GroupRunner(self._base_cls, self._plugins)

    def __repr__(self):
        return self._base_cls.__name__ + ': ' + repr(self._plugins)

    def __str__(self):
        return self._base_cls.__name__ + ': ' + str(list(self._plugins.keys()))

    def __getattribute__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            pass
        if item not in object.__getattribute__(self, '_plugins'):
            log.warning(item, 'plugin does not exist.', stack_offset=1)
            self._plugins[item] = Empty()
        return object.__getattribute__(self, '_plugins')[item]
