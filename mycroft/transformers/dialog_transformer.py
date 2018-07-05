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
from random import randint
from typing import Tuple

from mycroft.formatters.formatter_plugin import Format
from mycroft.package_cls import Package
from mycroft.transformers.transformer_plugin import TransformerPlugin
from mycroft.util import log
from mycroft.util.misc import warn_once


class DialogTransformer(TransformerPlugin):
    """Format data into sentences"""

    _package_struct = {
        'speech': str,
        'text': str
    }

    def __init__(self, rt):
        super().__init__(rt)
        self.rt.package.speech = self.rt.package.text = ''

    def process(self, p: Package):
        if not p.action:
            return
        locale_dir = self.rt.paths.skill_locale(skill_name=p.skill, lang=p.lang)
        file_base = join(locale_dir, p.action)
        speech = file_base + '.speech'
        dialog = file_base + '.dialog'
        text = file_base + '.text'

        line_id = -1

        if not p.speech:
            if isfile(speech):
                line_id, p.speech = self.render_file(speech, p, Format.speech, line_id)
            elif isfile(dialog):
                line_id, p.speech = self.render_file(dialog, p, Format.speech, line_id)
            else:
                p.speech = p.text
        if not p.text:
            if isfile(text):
                line_id, p.text = self.render_file(text, p, Format.text, line_id)
            elif isfile(dialog):
                line_id, p.text = self.render_file(dialog, p, Format.text, line_id)
            else:
                p.text = p.speech

        if not p.speech and not p.text:
            log.warning('No dialog at:', dialog)

    def render_file(self, filename: str, p: Package, fmt: Format, line_id = -1) -> Tuple[int, str]:
        best_lines, best_score = [], 0
        with open(filename) as f:
            lines = f.read().split('\n')

        for line in lines:
            if not line or line.isspace():
                continue

            line_score = 1
            for key, value in p.data.items():
                if value is None:
                    continue
                token = '{' + key + '}'
                if token in line:
                    line = line.replace(token, self.rt.formatter.format(value, fmt))
                    line_score += 1

            if re.search('{[a-zA-Z_]*}', line):
                line_score /= 100.
            if line_score > best_score:
                best_lines = [line]
                best_score = line_score
            elif line_score == best_score:
                best_lines.append(line)

        if 0 <= line_id < len(best_lines):
            choice_id = line_id
        else:
            choice_id = randint(0, len(best_lines) - 1)
        return choice_id, best_lines[choice_id]
