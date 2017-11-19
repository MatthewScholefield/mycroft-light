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

from mycroft.configuration import ConfigurationManager


class MycroftClient(metaclass=ABCMeta):
    """
    Provides common behavior like sending and receiving queries
    Examples clients include the voice client and text client
    """

    def __init__(self, path_manager, query_manager, formats):
        self.path_manager = path_manager
        self.formats = formats
        self._query_manager = query_manager
        self._query_manager.on_query(self.on_query)
        self._query_manager.on_response(self.on_response)
        self.global_config = ConfigurationManager.get()
        self.config = self.global_config.get(self.__class__.__name__)

    def send_query(self, query):
        """Ask a question and trigger on_response when an answer is found"""
        self._query_manager.send_query(query)

    @abstractmethod
    def run(self):
        """Executes the main thread for the client"""
        pass

    def on_query(self, query):
        """Called when any client sends query."""
        pass

    @abstractmethod
    def on_response(self, formats):
        """Called after send_query. Use FormatManager to get outputted response"""
        pass

    def on_exit(self):
        pass
