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
import re
from os.path import expanduser

from pkg_resources import Requirement, resource_filename

from mycroft.services.service_plugin import ServicePlugin


def find_refs(path):
    return re.findall('\${[a-zA-Z_]+}', path)


def get_var_name(ref):
    return ref.replace('${', '').replace('}', '')


def resolve_refs(config):
    while True:
        has_changed = False
        for var, path in config.items():
            refs = find_refs(str(path))
            for ref in refs:
                var_name = get_var_name(ref)
                if var_name in config:
                    path = path.replace(ref, config[var_name])
                    has_changed = True
            config[var] = path
        if not has_changed:
            break


class StringGetter:
    """Callable function that represents a path string with variables"""

    def __init__(self, path):
        self.path = path
        self.refs = find_refs(path)

    def __repr__(self):
        return self.path

    def __add__(self, other):
        return self.path + other

    def __radd__(self, other):
        return other + self.path

    def __call__(self, *args, **kwargs):
        kwargs.update(dict(zip([get_var_name(s) for s in self.refs], map(str, args))))

        path = self.path
        for ref in self.refs:
            var = get_var_name(ref)
            if var in kwargs:
                path = path.replace(ref, kwargs[var])
        return path


class PathsService(ServicePlugin):
    """
    An object that represents the data in mycroft.conf['paths']

    Usage:
    paths.skills  # /home/user/.mycroft/skills
    paths.skill_vocab('my_skill')  # /home/user/.mycroft/skills/my_skill/vocab/en-us

    paths.<CONFIG_KEY>(my_var=value)
    """

    def __init__(self, rt):
        super().__init__(rt)
        self.config = self.config.copy()
        self.config['data'] = resource_filename(Requirement.parse('mycroft-light'), 'mycroft/data')
        self.config['lang'] = self.rt.config['lang']

        resolve_refs(self.config)

        for k, v in self.config.items():
            self.config[k] = v.replace('~', expanduser('~'))

        for k, v in self.config.items():
            if find_refs(v):
                self.config[k] = StringGetter(v)

    def __getattr__(self, item):
        if item in self.config:
            return self.config[item]
        raise AttributeError("'" + item + "' not in paths config")
