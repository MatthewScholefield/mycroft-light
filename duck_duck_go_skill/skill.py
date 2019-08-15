# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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

import ddg3

from mycroft_core import MycroftSkill, intent_prehandler, Package
from mycroft.util import log
from mycroft.util.text import split_sentences, compare
import re


class DuckDuckGoSkill(MycroftSkill):
    """Fallback skill that queries DuckDuckGo's instant answer API"""
    articles = ['a', 'an', 'the', 'any']  # Should not be localized since they are used to parse
    # English API response

    def __init__(self):
        super().__init__()
        self.context = self.intent_context(['question'])
        self.start_words = self.locale('start_words.voc')

    def parse_related(self, p: Package, definition, query):
        p.data['raw_definition'] = definition
        ans = split_sentences(definition)[0]

        if ans[-2:] == '..':
            while ans[-1] == '.':
                ans = ans[:-1]

            phrases = ans.split(', ')
            first = ', '.join(phrases[:-1])
            last = phrases[-1]
            if last.split()[0] in self.start_words and len(phrases) < 3:
                ans = first
            last_word = ans.split(' ')[-1]
            while last_word in self.start_words or last_word[-3:] == 'ing':
                ans = ans.replace(' ' + last_word, '')
                last_word = ans.split(' ')[-1]

        match = re.search('\(([a-z ]+)\)', ans)
        if match:
            start, end = match.span(1)
            if start <= len(query) * 2:
                category = match.group(1)
                ans = ans.replace('(' + category + ')', '')
                p.data['category'] = category

        words = ans.split()
        sent_words = words[1:4 * len(query.split())]
        for article in self.articles:
            article = article.title()
            if article in sent_words:
                index = 1 + sent_words.index(article)
                name, desc = words[:index], words[index:]
                desc[0] = desc[0].lower()
                p.data['query'] = ' '.join(name)
                ans = ' '.join(desc)
                break
        else:
            for word in self.start_words + [query]:
                if words[0] == word.title():
                    p.data['query'] = None
                    if words[0] == words[1]:
                        ans = ' '.join(words[1:])

        if ans and ans[-1] not in '.?!':
            ans += '.'
        p.data['definition'] = ans

    @intent_prehandler('question', '')
    def ask_question(self, p: Package):
        intents = self.context.calc_intents(p.match.query)
        if not intents:
            return p.add(confidence=0.0)

        query = intents[0]['thing']
        r = ddg3.query(query)

        p.data['type'] = r.type
        p.confidence = 0.75

        log.debug('Query: ' + query)
        log.debug('Type: ' + r.type)

        if r.answer is not None and "HASH" not in r.answer.text:
            self.parse_related(p, r.answer.text, query)
        elif len(r.abstract.text) > 0:
            self.parse_related(p, r.abstract.text, query)
        elif len(r.related) > 0 and len(r.related[0].text) > 0:
            self.parse_related(p, r.related[0].text, query)
        else:
            return p.add(confidence=0.0)

        p.data.setdefault('query', query.title())
        p.faceplate.eyes.color = (200, 250, 0)

        return p
