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

import json
from tornado import websocket, web
from tornado.ioloop import IOLoop
from websocket import WebSocketApp

from mycroft.clients.mycroft_client import MycroftClient

clients = []


class SocketHandler(websocket.WebSocketHandler):
    def on_message(self, message):
        for c in clients:
            if c is not self:
                c.write_message(message)

    def open(self):
        clients.append(self)

    def on_close(self):
        clients.remove(self)


class WebsocketClient(MycroftClient):
    HOST='127.0.0.1'
    PORT=8017

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_server()
        self.t = None
        self.client = self.create_client()

    @staticmethod
    def start_server():
        application = web.Application(handlers=[('/', SocketHandler)])
        application.listen(8017, '127.0.0.1')

        Thread(target=IOLoop.current().start, daemon=True).start()

    def create_client(self):
        """Creates a websocket app to communicate with the Padatious process"""

        def on_message(server, message):
            self.send_query(message)

        client = WebSocketApp(url='ws://127.0.0.1:8017/', on_message=on_message)
        return client

    def run(self):
        self.client.run_forever()

    def on_query(self, query):
        self.client.send(json.dumps({'query': query}))

    def on_response(self, formats):
        self.client.send(json.dumps({'response': formats.dialog.get()}))
