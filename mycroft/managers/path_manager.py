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
import mycroft
from os.path import join, expanduser, abspath, dirname

from mycroft.configuration import ConfigurationManager
from mycroft.util.text import to_snake


class PathManager:
    """Retreives directories and files used by Mycroft"""

    def __init__(self):
        self.config = ConfigurationManager.get()
        self.lang = self.config['lang']

    @property
    def user_dir(self):
        return join(expanduser('~'), '.mycroft')

    @property
    def mimic_dir(self):
        return join(self.user_dir, 'mimic')

    @property
    def mimic_exe(self):
        return join(self.mimic_dir, 'mimic')

    @property
    def tts_cache(self):
        return self.config['tts']['temp_file']

    @property
    def intent_cache(self):
        return join(self.user_dir, 'intent_cache')

    def play_wav_cmd(self, file):
        return self.config['play_wav_cmdline'].replace('%1', file)

    @property
    def model_dir_no_lang(self):
        return join(self.user_dir, 'model')

    @property
    def model_dir(self):
        return join(self.model_dir_no_lang, self.lang)

    @property
    def data_dir(self):
        return join(abspath(mycroft.__path__[0]), 'data')

    @property
    def vocab_dir(self):
        return join(self.data_dir, 'vocab', self.lang)

    @property
    def sounds_dir(self):
        return join(self.data_dir, 'sounds')

    @property
    def padatious_dir(self):
        return join(self.user_dir, 'padatious')

    @property
    def padatious_exe(self):
        """The locally compiled Padatious executable"""
        return join(self.padatious_dir, 'build', 'src', 'padatious-mycroft')

    @property
    def skills_dir(self):
        return expanduser(self.config['skills']['directory'])

    def skill_dir(self, skill_name):
        return join(self.skills_dir, to_snake(skill_name))

    def skill_vocab_dir(self, skill_name):
        return join(self.skill_dir(skill_name), 'vocab', self.lang)

    def formats_dir(self, skill_name):
        return join(self.skill_dir(skill_name), 'formats')

    def intent_dir(self, skill_name):
        return self.skill_vocab_dir(skill_name)

    def dialog_dir(self, skill_name):
        return self.skill_vocab_dir(skill_name)

    def skill_conf(self, skill_name):
        return join(self.skill_dir(skill_name), 'skill.conf')
