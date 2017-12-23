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
from threading import Thread

from mycroft.managers.manager_plugin import ManagerPlugin
from mycroft.util import log
from mycroft.util.misc import safe_run


class QueryManager(ManagerPlugin):
    """Launches queries in separate threads"""

    def __init__(self, rt):
        super().__init__(rt)
        self.threads = []
        self.on_query_callbacks = []
        self.on_response_callbacks = []

    def _run_query(self, query):
        """Function to run query in a separate thread"""
        for i in self.on_query_callbacks:
            safe_run(lambda: i(query))
        safe_run(self.send_package, args=[self.rt.intent.calc_result(query)], warn=False)

    def send_package(self, package):
        """Generates data in all the formats and gives that formatted data to each callback"""

        self.rt.formats.generate(package.action, package.data)
        log.debug('Dialog:', self.rt.formats.dialog.get())
        if package.reset_event is not None:
            self.rt.formats.set_reset_event(package.reset_event)
        threads = []

        def mklm(fn):
            def ca():
                fn(self.rt.formats)

            return ca

        for resp_callback in self.on_response_callbacks:
            threads.append(Thread(target=safe_run, args=(mklm(resp_callback),)))

        for i in threads:
            i.start()

        for i in threads:
            i.join()

        self.rt.formats.reset()

    def send(self, query):
        """Starts calculating a query in a new thread"""
        t = Thread(target=self._run_query, args=(query,))
        t.start()
        self.threads.append(t)

    def on_query(self, callback):
        """Assign a callback to be run whenever a new response comes in"""
        self.on_query_callbacks.append(callback)

    def on_response(self, callback):
        """Assign a callback to be run whenever a new response comes in"""
        self.on_response_callbacks.append(callback)
