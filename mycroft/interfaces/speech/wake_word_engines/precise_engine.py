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
import platform
from os.path import join
from shutil import which
from typing import Callable

from mycroft.interfaces.speech.wake_word_engines.wake_word_engine_plugin import WakeWordEnginePlugin
from mycroft.util import log
from mycroft.util.misc import download_extract_tar


class PreciseEngine(WakeWordEnginePlugin):
    update_freq = 24  # in hours
    program_url = (
        'https://raw.githubusercontent.com/MycroftAI/'
        'precise-data/dist/{arch}/precise-engine.tar.gz'
    )
    model_url = (
        'https://raw.githubusercontent.com/MycroftAI/'
        'precise-data/models/{model_name}.tar.gz'
    )
    exe_name = 'precise-engine'

    def __init__(self, rt, on_activation: Callable):
        super().__init__(rt, on_activation)

        exe_file = which(self.exe_name)
        precise_folder = join(self.rt.paths.user_config, 'precise')
        if not exe_file:
            def on_update():
                self.rt.interfaces.faceplate.text('Updating listener...')

            def on_complete():
                self.rt.interfaces.faceplate.reset()

            download_extract_tar(self.program_url.format(arch=platform.machine()),
                                 precise_folder, check_md5=False, subdir='precise-engine',
                                 on_update=on_update, on_complete=on_complete)

            exe_file = join(precise_folder, 'precise-engine', 'precise-engine')
        log.debug('Precise executable location: ' + exe_file)

        model_folder = join(precise_folder, 'models', self.wake_word)
        download_extract_tar(self.model_url.format(model_name=self.wake_word),
                             model_folder, check_md5=True)

        from precise_runner import PreciseRunner, PreciseEngine
        engine = PreciseEngine(exe_file, join(model_folder, self.wake_word + '.pb'), chunk_size=1024)
        self.runner = PreciseRunner(engine, on_activation=on_activation)

    def start(self):
        print('START HERE')
        self.runner.start()

    def stop(self):
        self.runner.stop()
