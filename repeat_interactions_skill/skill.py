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
from mycroft_core import MycroftSkill, Package, intent_handler


class RepeatInteractionsSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.last_stts = [None]
        self.last_ttss = [None]
        self.rt.query.on_query(self.on_query)
        self.rt.query.on_response(self.on_response)
        self.owns_response = False

    def shutdown(self):
        self.rt.query.remove_on_query(self.on_query)
        self.rt.query.remove_on_response(self.on_response)

    def on_query(self, query):
        if query:
            self.last_stts.append(query)

    def on_response(self, p: Package):
        if self.owns_response:
            self.owns_response = False
            return
        self.last_ttss.append(p.speech)

    def on_handler(self):
        if len(self.last_stts) > 0:
            self.last_stts.pop(-1)
        self.owns_response = True

    @intent_handler('what.did.i.say')
    def what_did_i_say(self, p: Package):
        self.on_handler()
        p.data.update({
            'text': self.last_stts[-1]
        })

    @intent_handler('before.that')
    def before_that(self, p: Package):
        self.on_handler()
        self.what_did_i_say(p)

    @intent_handler('what.did.you.say')
    def what_did_you_say(self, p: Package):
        self.on_handler()
        p.data.update({
            'text': self.last_ttss[-1]
        })
