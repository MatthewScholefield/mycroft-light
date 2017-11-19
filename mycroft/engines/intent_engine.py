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

from abc import ABCMeta, abstractmethod

from mycroft.intent_name import IntentName


class IntentMatch:
    """An object that describes the how a query fits into a particular intent"""

    def __init__(self, name=IntentName(), confidence=0.0, matches={}, query=''):
        self.name = name
        self.confidence = confidence
        self.matches = matches
        self.query = query

    @classmethod
    def merge(cls, match_a, match_b):
        return match_a if match_a.confidence > match_b.confidence else match_b

    @classmethod
    def from_dict(cls, dict):
        return cls(IntentName.from_str(dict['name']), dict['confidence'], dict['matches'])


class IntentEngine(metaclass=ABCMeta):
    """Interface for intent engines"""

    def __init__(self, path_manager):
        self.path_manager = path_manager

    @abstractmethod
    def try_register_intent(*args, **kwargs):
        """
        Attempt to register intent with given arguments
        Returns:
            name (str): intent name if parsed parameters, otherwise ""
        """
        pass

    @abstractmethod
    def calc_intents(self, query):
        """
        Run the intent engine to determine the probability of each intent against the query
        Args:
            query (str): input sentence as a single string
        Returns:
            intent matches (list<IntentMatch>): describes how the intent engine matched each intent with the query
        """
        pass

    def on_intents_loaded(self):
        """Override to run code when all intents have been registered"""
        pass
