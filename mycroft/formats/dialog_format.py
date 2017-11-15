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
from random import randint

from mycroft.formats.mycroft_format import MycroftFormat


class DialogFormat(MycroftFormat):
    """Format data into sentences"""

    def __init__(self, path_manager):
        """
        Attributes:
            output  The most recent generated sentence
        """
        super().__init__('.dialog', 'dialog', path_manager)
        self.output = ""

    def get(self):
        return self.output

    def _reset(self):
        self.output = ""

    def _generate_format(self, file, results):
        lines = [(line, 0) for line in file.readlines()]
        for key, val in results.items():
            lines = [(i.replace('{' + key + '}', val), c + 1 if '{' + key + '}' in i else 0) for i, c in lines]
        best_lines = [i for i in lines if '{' not in i[0] and '}' not in i[0]]
        if len(best_lines) == 0:
            best_lines = [line for line, count in lines]
        else:
            index, max_count = max(best_lines, key=lambda item: item[1])
            best_lines = [line for line, count in best_lines if count == max_count]

        # Remove lines of only whitespace
        best_lines = [i for i in [i.strip() for i in best_lines] if i]

        self.output = best_lines[randint(0, len(best_lines) - 1)]
