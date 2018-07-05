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
from functools import wraps
from importlib import import_module
from os.path import abspath
from typing import Any, Type

from mycroft.plugin.base_plugin import BasePlugin
from mycroft.plugin.util import load_class, Empty
from mycroft.util import log
from mycroft.util.misc import safe_run
from mycroft.util.parallel import run_ordered_parallel
from mycroft.util.text import to_snake


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
            gp_kwargs = GroupPlugin._extract_gp_kwargs(kwargs)
            return run_ordered_parallel(self._plugins, lambda plugin: getattr(plugin, fn_name),
                                        args=args, kwargs=kwargs, label='Running all.' + fn_name,
                                        **gp_kwargs)

        return method

    def __getattribute__(self, item) -> list:
        try:
            return super().__getattribute__(item)
        except AttributeError as e:
            raise AttributeError(
                "'{}' base class has no method '{}'".format(self._cls.__name__, item)
            ) from e


class GroupPlugin(metaclass=ABCMeta):
    def __init__(self, *args, gp_order=None, gp_blacklist=None, **kwargs):
        """
        Calls __init__ of all plugins, passing arguments to each plugin's __init__
        Args:
            gp_order (list): List of attribute names in load order.
                    Other attributes will be loaded after or where '*' is in list
            gp_alter_class (Callable):
        """
        gp_order = [i for i in (gp_order or []) if i not in (gp_blacklist or [])]
        self._plugins = {}
        if not isinstance(type(self), GroupMeta):
            raise RuntimeError('{} must have GroupMeta as a metaclass'.format(
                self.__class__.__name__
            ))

        self._classes = self._load_classes(self._package_, self._suffix_, gp_blacklist or [])

        gp_kwargs = self._extract_gp_kwargs(kwargs)
        alter_class = gp_kwargs.pop('alter_class', None)

        def get_function(cls: Type[BasePlugin]):
            def func(*args, **kwargs):
                def create_plugin(*args, **kwargs):
                    new_cls = (alter_class(cls) or cls) if alter_class else cls
                    instance = new_cls(*args, **kwargs)
                    self._plugins[self._make_name(new_cls)] = instance
                    return instance
                plugin = safe_run(
                    create_plugin, args=args, kwargs=kwargs,
                    label='Loading ' + cls._attr_name + self._suffix_,
                    custom_exception=NotImplementedError,
                    custom_handler=lambda e, l: log.info(l + ': Skipping disabled plugin')
                )
                if not plugin:
                    log.debug('Unloading partially loaded plugin:', cls._attr_name + self._suffix_)
                    self._on_partial_load(cls._attr_name)
                return plugin
            return func

        self._init_threads = run_ordered_parallel(
            self._classes, get_function, args=args, kwargs=kwargs,
            order=gp_order, **gp_kwargs
        )
        self.all = GroupRunner(self._base_, self._plugins)

    def _on_partial_load(self, plugin_name):
        """Override to specify behavior when a plugin gets partially loaded"""
        pass

    @staticmethod
    def _extract_gp_kwargs(kwargs):
        gp_kwargs = {}
        for name in list(kwargs):
            if name.startswith('gp_'):
                gp_kwargs[name.replace('gp_', '')] = kwargs.pop(name)
        return gp_kwargs

    def _load_classes(self, package, suffix, blacklist):
        classes = (
            load_class(
                package, suffix, mod_name[:-len(suffix)], getattr(self, '_plugin_path', '')
            )
            for folder in set(abspath(i) for i in import_module(package).__path__)
            for loader, mod_name, is_pkg in pkgutil.walk_packages([folder])
            if mod_name.endswith(suffix) and mod_name[:-len(suffix)] not in blacklist
        )
        return {
            cls._attr_name: cls for cls in classes if cls
        }

    def _make_name(self, cls):
        return to_snake(cls.__name__).replace(self._suffix_, '')

    def __repr__(self):
        return self._base_cls.__name__ + ': ' + repr(self._plugins)

    def __str__(self):
        return self._base_cls.__name__ + ': ' + str(list(self._plugins.keys()))

    def __getattr__(self, item) -> Any:
        if item.startswith('_'):
            raise AttributeError(item)
        if '_plugins' not in self.__dict__:
            raise AttributeError(item)
        if item not in self._plugins:
            log.warning(item, 'plugin does not exist.', stack_offset=1)
            self._plugins[item] = Empty()
        return self._plugins[item]

    def __getitem__(self, item) -> Any:
        return self._plugins[item]

    def __iter__(self):
        return iter(self._plugins)


class GroupMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        if '_plugins' not in obj.__dict__:
            raise RuntimeError('GroupPlugin.__init__(<args>) never called in {}.__init__'.format(
                cls.__name__
            ))
        return obj

    def __new__(mcs, name, bases, namespace, base, package, suffix):
        if GroupPlugin not in bases:
            raise RuntimeError('{} must inherit from GroupPlugin'.format(name))
        return super().__new__(mcs, name, bases, {
            '_base_': base,
            '_package_': package,
            '_suffix_': suffix,
            **namespace
        })

    def __init__(cls, name, bases, namespace, *_, **__):
        super().__init__(name, bases, namespace)
