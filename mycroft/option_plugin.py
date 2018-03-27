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
from importlib import import_module
from inspect import isclass

from mycroft.util import log
from mycroft.util.text import to_camel, to_snake


class OptionPlugin:
    def __init__(self, base_cls, package, suffix, default):
        self._suffix = suffix
        self._base_cls = base_cls
        self._package = package
        self._option = ''
        self._default = default

        self._class = None
        self._plugin = None

    def init(self, option, *args, **kwargs):
        self._class = self.load_class(option)
        if not self._class:
            return
        try:
            self._plugin = self._class(*args, **kwargs)
        except Exception:
            if self.make_name(self._class) != self._default:
                log.exception('Loading', self._class.__name__)
                self._option = self._default
                self.init_plugin(*args, **kwargs)
            else:
                raise

    def load_class(self, option):
        package = self._package + '.' + option + self._suffix
        log.debug('Loading', package + '...')
        try:
            mod = import_module(package)
            cls = getattr(mod, to_camel(option + self._suffix), '')
            if not isclass(cls):
                log.error('Class not callable:', cls)
            else:
                if hasattr(self, '_plugin_path'):
                    plugin_path = self._plugin_path + '.'
                else:
                    plugin_path = ''

                cls._attr_name = self.make_name(cls)
                cls._plugin_path = plugin_path + cls._attr_name
                return cls
        except Exception:
            log.exception('Loading Module', package)
        return None

    def make_name(self, cls):
        return to_snake(cls.__name__).replace(self._suffix, '')

    def __repr__(self):
        return self._base_cls.__name__ + ': ' + repr(self._plugin)

    def __str__(self):
        return self._base_cls.__name__ + ': ' + str(self._class and self._class.__name__)

    def __getattribute__(self, item):
        def raw_get(obj, attr):
            return object.__getattribute__(obj, attr)

        try:
            return raw_get(self, item)
        except AttributeError:
            return raw_get(raw_get(self, '_plugin'), item)
