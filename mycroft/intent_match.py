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


class MissingIntentMatch(KeyError):
    pass


class IntentMatch:
    """An object that describes the how a query fits into a particular intent"""

    def __init__(self, intent_id='', confidence=0.0, matches=None, query=''):
        self.intent_id = intent_id
        self.confidence = confidence
        self.matches = matches or {}
        self.query = query

    def __getitem__(self, item):
        try:
            return self.matches[item]
        except KeyError:
            pass
        raise MissingIntentMatch(item)

    def __contains__(self, item):
        return self.matches.__contains__(item)

    def __repr__(self):
        return '<IntentMatch intent_id={} confidence={} matches={} query={}>'.format(
            self.intent_id, self.confidence, self.matches, self.query
        )

    def __bool__(self):
        return any(bool(i) for i in [self.intent_id, self.confidence, self.matches, self.query])
