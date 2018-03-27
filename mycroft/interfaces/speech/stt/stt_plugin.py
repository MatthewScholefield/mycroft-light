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
from abc import abstractmethod

from speech_recognition import AudioData

from mycroft.base_plugin import BasePlugin


class SttPlugin(BasePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.lang = str(self._get_lang(rt.config))

        self.credential = self.config.get('credential', {})
        self.token = str(self.credential.get('token'))
        self.username = str(self.credential.get('username'))
        self.password = str(self.credential.get('password'))

    @staticmethod
    def _get_lang(config_core):
        lang = config_core.get('lang', 'en-US')
        langs = lang.split('-')
        if len(langs) == 2:
            return langs[0].lower() + '-' + langs[1].upper()
        return lang

    @abstractmethod
    def transcribe(self, audio: AudioData) -> str:
        """Internal function to overload. Returns transcription"""
        pass
