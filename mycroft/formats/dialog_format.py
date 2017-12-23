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

import random
import re

from mycroft.formats.format_plugin import FormatPlugin


class DialogFormat(FormatPlugin):
    """Format data into sentences"""

    def __init__(self, rt):
        """
        Attributes:
            output  The most recent generated sentence
        """
        super().__init__(rt, '.dialog')
        self.output = ""

    def get(self):
        return self.output

    def reset(self):
        self.output = ""

    def generate_format(self, file, results):
        best_lines, best_score = [], 0
        for line in file.read().split('\n'):
            if not line or line.isspace():
                continue

            line_score = 0
            for key in results:
                token = '{' + key + '}'
                if token in line:
                    line = line.replace(token, str(results[key]))
                    line_score += 1

            if re.search('{[a-zA-Z_]*}', line):
                line_score /= 100.
            if line_score > best_score:
                best_lines = [line]
                best_score = line_score
            elif line_score == best_score:
                best_lines.append(line)

        self.output = random.choice(best_lines)
