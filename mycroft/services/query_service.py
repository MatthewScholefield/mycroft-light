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
from threading import Thread, Event

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util import log
from mycroft.util.misc import safe_run
from mycroft.util.parallel import run_parallel


class QueryService(ServicePlugin):
    """Launches queries in separate threads"""

    def __init__(self, rt):
        super().__init__(rt)
        self.threads = []
        self.on_query_callbacks = []
        self.on_response_callbacks = []
        self.response_event = Event()
        self.query_consumer = None

    def _run_query(self, query):
        """Function to run query in a separate thread"""
        run_parallel(self.on_query_callbacks, label='Running query', args=[query])
        if self.query_consumer and query:
            self.query_consumer(query)
        else:
            safe_run(self.send_package, args=[self.rt.intent.calc_package(query)], warn=False)

    def send_package(self, package):
        """Generates various forms of the data and gives that formatted data to each callback"""

        self.rt.transformers.process(package)
        log.debug('Dialog:', package.speech)

        def mklm(fn):
            def ca():
                fn(package)

            return ca

        threads = [
            Thread(target=safe_run, args=(mklm(resp_callback),))
            for resp_callback in self.on_response_callbacks
        ]

        self.response_event.set()
        for i in threads:
            i.start()

        for i in threads:
            i.join()
        self.response_event.clear()

    def send(self, query):
        """Starts calculating a query in a new thread"""
        t = Thread(target=self._run_query, args=(query,))
        t.start()
        self.threads.append(t)

    def on_query(self, callback):
        """Assign a callback to be run whenever a new response comes in"""
        self.on_query_callbacks.append(callback)

    def remove_on_query(self, callback):
        self.on_query_callbacks.remove(callback)

    def remove_on_response(self, callback):
        self.on_response_callbacks.remove(callback)

    def get_next_query(self, timeout=None):
        """Waits for and consume next response"""
        on_query = Event()

        def consumer(query):
            consumer.query = query
            on_query.set()
        consumer.query = None

        self.query_consumer = consumer
        on_query.wait(timeout)
        self.query_consumer = None

        return consumer.query

    def on_response(self, callback):
        """Assign a callback to be run whenever a new response comes in"""
        self.on_response_callbacks.append(callback)
