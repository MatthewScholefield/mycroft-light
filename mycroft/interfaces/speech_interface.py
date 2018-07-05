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
from contextlib import suppress
from os.path import isfile

from requests.exceptions import RequestException

from mycroft.interfaces.interface_plugin import InterfacePlugin

from mycroft.interfaces.speech.recognizer_service import RecognizerService
from mycroft.interfaces.speech.stt_service import SttService
from mycroft.interfaces.speech.stt.stt_plugin import SttPlugin
from mycroft.util import log
from mycroft.util.audio import play_audio


class NewQuerySignal(Exception):
    pass


class SkipActivationSignal(Exception):
    pass


class SpeechInterface(InterfacePlugin):
    """Interact with Mycroft via a terminal"""
    _package_struct = {
        'skip_activation': bool
    }

    def __init__(self, rt):
        super().__init__(rt)
        self.stt = SttService(rt, self._plugin_path)  # type: SttPlugin
        RecognizerService._plugin_path = self._plugin_path + '.recognizer'
        RecognizerService._attr_name = 'recognizer'
        self.recognizer = RecognizerService(rt)

    def run(self):
        while not self.rt.main_thread.quit_event.is_set():
            try:
                with suppress(NewQuerySignal):
                    with suppress(SkipActivationSignal):
                        self.recognizer.wait_for_wake_word()
                    self.send_query(self.record_phrase())
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception:
                log.exception('In speech interface')

    def on_query(self, query):
        self.recognizer.intercept(NewQuerySignal)

    def on_response(self, package):
        if package.skip_activation:
            self.rt.interfaces.tts.wait()
            self.recognizer.intercept(SkipActivationSignal)

    def on_exit(self):
        self.recognizer.intercept(SystemExit)
        self.recognizer.on_exit()

    def record_phrase(self) -> str:
        """Record and transcribe a question from the user. Can raise NewQuerySignal"""
        self.rt.interfaces.faceplate.listen()
        self._play_sound(self.rt.paths.audio_start_listening)
        recording = self.recognizer.record_phrase()
        self._play_sound(self.rt.paths.audio_stop_listening)
        self.rt.interfaces.faceplate.reset()
        return self._get_transcription(recording)

    def _get_transcription(self, recording):
        utterance = ''
        try:
            utterance = self.stt.transcribe(recording)
        except ValueError:
            log.info('Found no words in audio')
        except RequestException:
            log.exception('Speech Client')
        else:
            log.info('Utterance: ' + utterance)
        return utterance

    @staticmethod
    def _play_sound(path):
        if isfile(path):
            play_audio(path)
