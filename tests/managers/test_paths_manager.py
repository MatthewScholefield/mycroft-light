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
import sys
sys.path += ['.']  # noqa

from unittest.mock import Mock
from mycroft.services.paths_service import resolve_refs, StringGetter
from mycroft.services import paths_service
PathsManager = paths_service.PathsService
paths_service.resource_filename = lambda *args: ''


class TestResolver:
    def test_1(self):
        config = {
            'this': 'is',
            'a test': None
        }
        orig = config.copy()
        resolve_refs(config)
        assert orig == config

    def test_2(self):
        config = {
            'a': '$b',
            'b': 'c'
        }
        resolve_refs(config)
        assert config == {'a': 'c', 'b': 'c'}

    def test_3(self):
        config = {
            'a': '1',
            'b': '2$a',
            'c': '$a/$b:$d'
        }
        resolve_refs(config)
        assert config == {'a': '1', 'b': '21', 'c': '1/21:$d'}


class TestStringGetter:
    def test_1(self):
        s = StringGetter('$a:$b')
        assert s(a='1', b='2') == '1:2'
        assert s(3, 4) == '3:4'


class TestPathsManager:
    def setup(self):
        self.rt = Mock()
        self.rt.config = {'lang': 'en-us'}
        PathsManager._attr_name = 'paths'

    def test_1(self):
        self.rt.config['paths'] = {'a': '1', 'b': '2$a'}
        assert PathsManager(self.rt).b == '21'

    def test_2(self):
        self.rt.config['paths'] = {'a': '1', 'b': '2$a', 'c': '$b$d'}
        assert str(PathsManager(self.rt).c) == '21$d'
        assert PathsManager(self.rt).c(3) == '213'



