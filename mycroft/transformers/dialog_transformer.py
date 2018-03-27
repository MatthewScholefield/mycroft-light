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

from os.path import isfile, join

from mycroft.package_cls import Package
from mycroft.transformers.transformer_plugin import TransformerPlugin
from mycroft.util.misc import warn_once


class DialogTransformer(TransformerPlugin):
    """Format data into sentences"""

    _package_struct = {
        'speech': str,
        'text': str
    }

    def process(self, p: Package):
        locale_dir = self.rt.paths.skill_locale(skill_name=p.skill, lang=p.lang)
        file_base = join(locale_dir, p.action)
        speech = file_base + '.speech'
        text = file_base + '.text'

        if not p.speech and not p.text:
            p.speech = p.text = ''

            if isfile(speech):
                p.speech = self.render_file(speech, p)
            if isfile(text):
                p.text = self.render_file(text, p)

        if not p.speech:
            p.speech = p.text
        if not p.text:
            p.text = p.speech

    def render_file(self, filename: str, p: Package) -> str:
        best_lines, best_score = [], 0
        with open(filename) as f:
            lines = f.read().split('\n')

        for line in lines:
            if not line or line.isspace():
                continue

            line_score = 0
            for key in p.data:
                token = '{' + key + '}'
                if token in line:
                    line = line.replace(token, str(p.data[key]))
                    line_score += 1

            if re.search('{[a-zA-Z_]*}', line):
                line_score /= 100.
            if line_score > best_score:
                best_lines = [line]
                best_score = line_score
            elif line_score == best_score:
                best_lines.append(line)

        return random.choice(best_lines)
