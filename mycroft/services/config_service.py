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
from genericpath import isfile
from os.path import join, expanduser

import yaml
from pkg_resources import Requirement, resource_filename
from typing import Callable

from mycroft.api import DeviceApi
from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log
from mycroft.util.text import to_snake

SYSTEM_CONFIG = '/etc/mycroft/mycroft.conf'
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')

REMOTE_CONFIG = 'mycroft.ai'
REMOTE_CACHE = join(expanduser('~'), '.mycroft/web_config_cache.yaml')
IGNORED_SETTINGS = ["uuid", "@type", "active", "user", "device"]

DEFAULT_CONFIG = resource_filename(Requirement.parse('mycroft-light'), 'mycroft/data/mycroft.conf')

LOAD_ORDER = [DEFAULT_CONFIG, REMOTE_CACHE, SYSTEM_CONFIG, USER_CONFIG]


class ConfigService(ServicePlugin, dict):
    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        dict.__init__(self)
        self.handlers = {}
        self.load_local()

    def load_remote(self, settings=None):
        log.debug('Loading remote config...')
        try:
            self.__store_cache(settings or DeviceApi(self.rt).get_settings())
            self.load_local()
        except ConnectionError:
            log.exception('Loading Remote Config')

    def _update(self, out, inp, pos):
        for i in inp:
            new_pos = pos + ('.' if pos else '') + i
            if i in out and isinstance(inp[i], dict) and isinstance(out[i], dict):
                self._update(out[i], inp[i], new_pos)
            else:
                out[i] = inp[i]
                if new_pos in self.handlers:
                    log.debug('Config has updated for {}...'.format(new_pos))
                    self.handlers[new_pos](out[i])
        if pos in self.handlers:
            log.debug('Config has updated for {}...'.format(pos))
            self.handlers[pos](out)

    def inject(self, config: dict, path: str = ''):
        """Recursively update with new config"""
        self._update(self.get_path(path), config, path)

    def get_path(self, path: str):
        """Recursively gets dot-separated path in config"""
        config = self
        if path:
            for i in path.split('.'):
                config = config.setdefault(i, {})
        return config

    def load_local(self):
        for file_name in LOAD_ORDER:
            if isfile(file_name):
                with open(file_name) as f:
                    self.inject(yaml.safe_load(f))

    def __conv(self, out, inp):
        """
        Converts remote config style to local config
        (Removes server specific entries)
        """
        for k, v in inp.items():
            if k not in IGNORED_SETTINGS:
                # Translate the CamelCase values stored remotely into the
                # Python-style names used within mycroft-core.
                key = to_snake(k.replace('Settings', '').replace('Setting', ''))
                if isinstance(v, dict):
                    out[key] = out.get(key, {})
                    self.__conv(out[key], v)
                elif isinstance(v, list):
                    if key not in out:
                        out[key] = {}
                    self.__conv_list(out[key], v)
                else:
                    out[key] = v

    def __conv_list(self, out, inp):
        for v in inp:
            mod = v["@type"]
            if v.get("active"):
                out["module"] = mod
            out[mod] = out.get(mod, {})
            self.__conv(out[mod], v)

    def __store_cache(self, setting):
        """Save last version of remote config for future use"""
        config = {}
        self.__conv(config, setting)
        with open(REMOTE_CACHE, 'w') as f:
            yaml.dump(config, f)

    def on_change(self, path: str, handler: Callable):
        self.handlers[path] = handler
