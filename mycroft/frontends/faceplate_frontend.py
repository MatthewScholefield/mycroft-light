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

from mycroft.frontends.frontend_plugin import FrontendPlugin
from mycroft.util import log


class FaceplateFrontend(FrontendPlugin):
    """Interact with Mycroft via the Mark 1 Enclosure"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        if not self.rt.formats.faceplate:
            return
        Thread(target=self.rt.formats.faceplate.run, daemon=True).start()
        while not self.rt.main_thread.exit_event.is_set():
            line = self.rt.formats.faceplate.readline()
            if 'volume.up' in line:
                self.rt.skills.volume.increase_volume()
            elif 'volume.down' in line:
                self.rt.skills.volume.decrease_volume()
            elif 'Command: ' in line:
                pass  # Reply from Arduino
            elif len(line.strip()) > 0:
                log.warning('Could not handle message: ' + line)

    def on_response(self, formats):
        pass
