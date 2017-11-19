#
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
#
import re
from genericpath import isfile
from os.path import join, expanduser

import yaml
from pkg_resources import Requirement, resource_filename
from twiggy import log
from mycroft.util.text import to_snake

SYSTEM_CONFIG = '/etc/mycroft/mycroft.conf'
USER_CONFIG = join(expanduser('~'), '.mycroft/mycroft.conf')

REMOTE_CONFIG = 'mycroft.ai'
REMOTE_CACHE = '/opt/mycroft/web_config_cache.yaml'
IGNORED_SETTINGS = ["uuid", "@type", "active", "user", "device"]

DEFAULT_CONFIG = resource_filename(Requirement.parse('mycroft-light'), 'mycroft/data/mycroft.conf')

LOAD_ORDER = [DEFAULT_CONFIG, REMOTE_CACHE, SYSTEM_CONFIG, USER_CONFIG]


class ConfigurationManager:
    __config = {}

    @classmethod
    def init(cls):
        cls.load_local()

    @classmethod
    def load_remote(cls):
        from mycroft.api import DeviceApi

        cls.__store_cache(DeviceApi().get_settings())
        cls.load_local()

    @classmethod
    def _update(cls, out, inp):
        """Recursive update inp into out"""
        for i in inp:
            if i in out and isinstance(inp[i], dict) and isinstance(out[i], dict):
                cls._update(out[i], inp[i])
            else:
                out[i] = inp[i]

    @classmethod
    def load_local(cls):
        cls.__config = {}

        for file_name in LOAD_ORDER:
            if isfile(file_name):
                log.info('Loading ' + file_name + '...')
                with open(file_name) as f:
                    cls._update(cls.__config, yaml.safe_load(f))
            else:
                log.info('Skipping ' + file_name + '...')

    @classmethod
    def get(cls):
        return cls.__config

    @staticmethod
    def load_skill_config(conf_file):
        if isfile(conf_file):
            with open(conf_file, 'r') as f:
                return yaml.safe_load(f)
        return {}

    @classmethod
    def __conv(cls, out, inp):
        """
        Converts remote config style to local config
        (Removes server specific entries)
        """
        for k, v in inp.items():
            if k not in IGNORED_SETTINGS:
                # Translate the CamelCase values stored remotely into the
                # Python-style names used within mycroft-core.
                key = to_snake(re.sub(r"Setting(s)?", "", k))
                if isinstance(v, dict):
                    out[key] = out.get(key, {})
                    cls.__conv(out[key], v)
                elif isinstance(v, list):
                    if key not in out:
                        out[key] = {}
                    cls.__conv_list(out[key], v)
                else:
                    out[key] = v

    @classmethod
    def __conv_list(cls, out, inp):
        for v in inp:
            mod = v["@type"]
            if v.get("active"):
                out["module"] = mod
            out[mod] = out.get(mod, {})
            cls.__conv(out[mod], v)

    @classmethod
    def __store_cache(cls, setting):
        """Save last version of remote config for future use"""
        config = {}
        cls.__conv(config, setting)
        with open(REMOTE_CACHE, 'w') as f:
            yaml.dump(config, f)
