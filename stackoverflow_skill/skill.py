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

from mycroft import MycroftSkill
from stackexchange import StackOverflow, Site
from lxml import html
import re

from mycroft.util import log


class StackoverflowSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.so = Site(StackOverflow)
        self.so.be_inclusive()
        self.register_intent('ask', self.ask)

    def ask(self, data):
        questions = self.so.search(intitle=data.query)
        self.add_result('query', data.query)

        for question in questions:
            question.fetch()
            if len(question.answers) > 0:
                answer = question.answers[0]
                text_answer = html.fromstring(answer.body).text_content()
                self.add_result('question_title', question.title)
                self.add_result('question_body_html', question.body)
                self.add_result('question_body_text', html.fromstring(question.body).text_content())
                self.add_result('answer_html', answer.body)
                self.add_result('answer_text', text_answer)
                try:
                    short = re.sub('</?code>', '', max(re.findall('<code>[\s\S]*?</code>', answer.body), key=len))
                except IndexError:
                    log.debug("Couldn't find code")
                    short = text_answer.split('\n')[0] if '\n' in text_answer else text_answer
                log.debug('Answer Body: ' + answer.body)
                self.add_result('answer_short', short)
                return 0.8
        self.set_action('not.found')
        return 0.4
