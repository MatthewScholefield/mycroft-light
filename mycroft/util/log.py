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

import time
import twiggy
from twiggy.outputs import FileOutput
from twiggy.filters import Emitter


def pretty_time(gmtime=None):
    return time.strftime('%y.%m.%d - %H:%M:%S', gmtime if gmtime else time.gmtime())


def setup_logging(config):
    format = twiggy.formats.LineFormat(' : ', '\n')
    format.conversion.get('time').convert_value = pretty_time
    format.conversion.aggregate = ' : '.join
    output = FileOutput(config['log_file'], format, 'w')
    twiggy.emitters['*'] = Emitter(twiggy.levels.name2level(config['log_level']), True, output)
