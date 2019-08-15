# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
from difflib import SequenceMatcher
from typing import Iterable, Tuple


def to_camel(snake):
    """time_skill -> TimeSkill"""
    return snake.title().replace('_', '')


def to_snake(camel):
    """TimeSkill -> time_skill"""
    if not camel:
        return camel
    return ''.join('_' + x if 'A' <= x <= 'Z' else x for x in camel).lower()[camel[0].isupper():]


def compare(a: str, b: str) -> float:
    return SequenceMatcher(a=a.lower(), b=b.lower()).ratio()


def find_match(query: str, options: Iterable[str]) -> Tuple[str, float]:
    return max([(option, compare(option, query)) for option in options], key=lambda x: x[1])


def split_sentences(text):
    """
    Turns a string of multiple sentences into a list of separate ones
    As a side effect, .?! at the end of a sentence are removed
    """
    sents = list(filter(bool, text.split('. ')))

    # Rejoin sentences with an initial
    # ['Harry S', 'Truman'] -> ['Harry S. Truman']
    i = 0
    corrected_sents = []
    while i < len(sents):
        if len(sents[i].split()[-1]) <= 3 and i < len(sents) - 1:
            corrected_sents += [sents[i] + '. ' + sents[i + 1]]
            i += 2
        else:
            corrected_sents += [sents[i]]
            i += 1

    sents = corrected_sents

    for punc in ['?', '!']:
        new_sents = []
        for i in sents:
            new_sents += i.split(punc + ' ')
        sents = new_sents

    return sents
