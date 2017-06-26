#
# Copyright (c) 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Simple
# (see https://github.com/MatthewScholefield/mycroft-simple).
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
import ddg3

from mycroft.mycroft_skill import MycroftSkill
from mycroft.util import split_sentences


class DuckDuckGoSkill(MycroftSkill):
    """Fallback skill that queries DuckDuckGo's instant answer API"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_fallback(self.fallback)
        self.register_fallback(self.fallback_no_question)

    def fallback(self, query):
        r = ddg3.query(query)

        conf = 1.0

        if r.type == 'answer':
            if len(r.abstract.text) > 0:
                sents = split_sentences(r.abstract.text)
                self.add_result('abstract', sents[0])
                if len(sents) > 1:
                    self.add_result('abstract_full', r.abstract.text)
            else:
                conf *= 0.0
        elif r.type == 'exclusive':  # Like answer to 1 + 1
            if len(r.answer.text) == 0 or "HASH" in r.answer.text:
                conf *= 0
            else:
                self.add_result('answer', r.answer.text)
        elif r.type == 'disambiguation':
            conf *= 0.7
            if len(r.related) == 0 or len(r.related[0].text) == 0:
                conf *= 0.0
            else:
                abstract = split_sentences(r.related[0].text)[0]
                if abstract[-3:] == '...':
                    conf *= 0.8

                num_words = len(abstract.split(' '))
                if num_words < 5:
                    conf *= num_words / 5.0
                self.add_result('abstract', abstract)
        else:
            conf *= 0.0

        self.add_result('query', query)
        self.add_result('type', r.type)
        self.add_result('confidence', conf)

    def fallback_no_question(self, query):
        orig_query = query
        for noun in ['what', 'who', 'when']:
            for verb in [' is', '\'s', 's', ' are', '\'re', 're', ' did', ' was', ' were']:
                test = noun + verb
                if query[:len(test)] == test:
                    query = query[len(test):]

        if query != orig_query:
            self.fallback(query)
        else:
            self.add_result('confidence', 0.0)
