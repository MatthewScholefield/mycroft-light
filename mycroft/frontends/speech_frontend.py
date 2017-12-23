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

from os.path import join, isfile

from requests.exceptions import ReadTimeout, HTTPError

from mycroft.frontends.frontend_plugin import FrontendPlugin
from mycroft.frontends.speech.recognizers.recognizer_plugin import RecognizerPlugin
from mycroft.frontends.speech.stt.stt_plugin import SttPlugin
from mycroft.option_plugin import OptionPlugin
from mycroft.util import log
from mycroft.util.audio import play_audio


class NewQuerySignal(Exception):
    pass

class SkipActivationSignal(Exception):
    pass


class SpeechFrontend(FrontendPlugin):
    """Interact with Mycroft via a terminal"""

    def __init__(self, rt):
        super().__init__(rt)
        self.exit = False
        self.recognizer = self.create_recognizer()
        self.stt = self.create_stt()
        self.start_listening_file = join(self.rt.paths.audio_start_listening)
        self.stop_listening_file = join(self.rt.paths.audio_stop_listening)

    def create_recognizer(self) -> RecognizerPlugin:
        r = OptionPlugin(RecognizerPlugin, 'mycroft.frontends.speech.recognizers',
                         '_recognizer', 'pocketsphinx')
        r.plugin_path = self.plugin_path + '.recognizers'
        r.init(self.config['recognizers']['module'], self.rt)
        return r

    def create_stt(self):
        stt = OptionPlugin(SttPlugin, 'mycroft.frontends.speech.stt', '_stt', 'mycroft')
        stt.plugin_path = self.plugin_path + '.stt'
        stt.init(self.config['stt']['module'], self.rt)
        return stt

    def run(self):
        try:
            while not self.rt.main_thread.quit_event.is_set():
                try:
                    log.info('Waiting for wake word...')
                    try:
                        self.recognizer.wait_for_wake_word()
                    except SkipActivationSignal:
                        pass

                    self.rt.formats.faceplate.command('mouth.listen')
                    if isfile(self.start_listening_file):
                        play_audio(self.start_listening_file)

                    log.info('Recording...')
                    recording = self.recognizer.record_phrase()
                    log.info('Done recording.')

                    self.rt.formats.faceplate.command('mouth.reset')
                    if isfile(self.stop_listening_file):
                        play_audio(self.stop_listening_file)

                    try:
                        utterance = self.stt.transcribe(recording)
                    except (HTTPError, ValueError, ReadTimeout):
                        log.exception('Speech Client')
                        utterance = ''
                    log.info('Utterance: ' + utterance)

                    self.send_query(utterance)
                except NewQuerySignal:
                    pass
        except SystemExit:
            pass

    def on_query(self, query):
        log.debug('INTERCEPT query...')
        self.recognizer.intercept(NewQuerySignal)

    def on_response(self, formats):
        if formats.client.get('skip_activation', False):
            self.rt.frontends.tts.wait()
            self.recognizer.intercept(SkipActivationSignal)

    def on_exit(self):
        self.exit = True
        self.recognizer.intercept(SystemExit)
        self.recognizer.on_exit()
