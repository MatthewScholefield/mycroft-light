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
from requests import HTTPError
from speech_recognition import Recognizer, UnknownValueError, RequestError

from mycroft.api import STTApi
from mycroft.configuration import ConfigurationManager


def init_mycroft(self):
    self.api = STTApi()


init_callbacks = {
    'mycroft': init_mycroft
}


def execute_mycroft(self, audio):
    try:
        result = self.api.stt(audio.get_flac_data(), self.lang, 1)
    except HTTPError:
        raise RequestError
    if len(result) == 0:
        raise UnknownValueError
    return result[0]


execute_callbacks = {
    'mycroft': execute_mycroft,
    'google': lambda self, audio: self.recognizer.recognize_google(audio, self.token, self.lang),
    'wit': lambda self, audio: self.recognizer.recognize_wit(audio, self.token),
    'ibm': lambda self, audio: self.recognizer.recognize_ibm(audio, self.username, self.password, self.lang)
}


class STT:
    def __init__(self):
        config_core = ConfigurationManager.get()
        tts_name = config_core.get('stt', {}).get('module', 'mycroft')

        init_callbacks.get(tts_name, lambda _: None)(self)
        self.on_execute = execute_callbacks[tts_name]

        self.lang = str(self._get_lang(config_core))
        config_stt = config_core.get('stt', {})
        self.config = config_stt.get(config_stt.get('module'), {})
        self.credential = self.config.get('credential', {})
        self.recognizer = Recognizer()

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

    def execute(self, audio):
        try:
            return self.on_execute(self, audio)
        except (UnknownValueError, RequestError):
            return ''
