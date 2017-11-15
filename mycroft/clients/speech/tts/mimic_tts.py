#
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
#
from os.path import join, isfile
from subprocess import check_output

from mycroft.clients.speech.tts.mycroft_tts import MycroftTTS
from mycroft.util.git_repo import GitRepo


class MimicTTS(MycroftTTS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mimic_repo = GitRepo(directory=self.path_manager.mimic_dir,
                                  url='https://github.com/MycroftAI/mimic.git',
                                  branch='1.2.0.2',
                                  update_freq=24)
        self.script_repo = GitRepo(directory=join(self.mimic_repo.dir, 'scripts'),
                                   url='https://github.com/MatthewScholefield/mycroft-light.git',
                                   branch='mimic-script',
                                   update_freq=24)

        mimic_change = self.mimic_repo.try_pull()
        script_change = self.script_repo.try_pull()

        if mimic_change or script_change or not isfile(self.path_manager.mimic_exe):
            self.mimic_repo.run_inside(['sh', join('scripts', 'build-mimic.sh')])

    def speak(self, text):
        phonemes = check_output([self.path_manager.mimic_exe, '-t', text, '-o', self.path_manager.tts_cache, '-psdur'])
        self.speak_wav(self.path_manager.tts_cache, phonemes.decode())