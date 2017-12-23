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
from mycroft.base_plugin import BasePlugin


class FrontendPlugin(BasePlugin):
    """
    Provides common behavior like sending and receiving queries
    Example frontends include the voice frontend and text frontend
    """

    def __init__(self, rt):
        super().__init__(rt)
        rt.query.on_query(self.on_query)
        rt.query.on_response(self.on_response)

    def send_query(self, query):
        """Helper to ask questions"""
        self.rt.query.send(query)

    def on_query(self, query):
        """Called when any frontend sends query."""
        pass

    def on_response(self, formats):
        """Called after send_query. Use FormatManager to get outputted response"""
        pass

    def run(self):
        """Executes the main thread for the frontend"""
        pass

    def on_exit(self):
        pass
