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
from abc import ABCMeta

from mycroft.plugin.util import load_class, load_plugin
from mycroft.util import log
from mycroft.util.text import to_snake


class MustOverride(NotImplementedError):
    pass


class OptionPlugin:
    def __init__(self, *args, __module__, **kwargs):
        self._plugin = None
        if not isinstance(type(self), OptionMeta):
            raise RuntimeError('{} must have OptionMeta as a metaclass'.format(
                self.__class__.__name__
            ))
        self._class, self._plugin = self.__load_plugin(__module__, args, kwargs)
        self.__copy_functions(self._plugin)

        log.info('Loaded {} as {}.'.format(self._class.__name__, self.__class__.__name__))

    def __load_plugin(self, module, args, kwargs):
        package, suffix, default = self._package_, self._suffix_, self._default_
        plugin_path = getattr(self, '_plugin_path', '')

        cls = load_class(package, suffix, module, plugin_path)
        plugin = load_plugin(cls, args, kwargs)
        if not plugin and module != default:
            cls = load_class(package, suffix, default, plugin_path)
            plugin = load_plugin(cls, args, kwargs)

        if not plugin:
            raise RuntimeError('Both modules failed to load for {}'.format(self.__class__.__name__))

        return cls, plugin

    def __copy_functions(self, obj):
        for name in dir(obj):
            if not name.startswith('_'):
                value = getattr(obj, name)
                if callable(value):
                    setattr(self, name, value)

    def __getattr__(self, item):
        if item.startswith('_'):
            raise AttributeError(item)
        return getattr(self._plugin, item)

    def __str__(self):
        return self._base_class.__name__ + ': ' + str(self._plugin)

    def __repr__(self):
        return self._base_class.__name__ + ': ' + repr(self._plugin)


class OptionMeta(ABCMeta):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        if not hasattr(obj, '_plugin'):
            raise RuntimeError('OptionPlugin.__init__(<args>) never called in {}.__init__'.format(
                cls.__name__
            ))
        return obj

    def __new__(mcs, name, bases, namespace, base, package, suffix, default):
        return super().__new__(mcs, name, bases, {
            '_base_': base,
            '_package_': package,
            '_suffix_': suffix,
            '_default_': default,
            **namespace
        })

    def __init__(cls, name, bases, namespace, *_, **__):
        super().__init__(name, bases, namespace)
