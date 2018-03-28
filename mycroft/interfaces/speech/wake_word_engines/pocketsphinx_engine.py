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

import os
import tempfile
from os.path import join
from typing import Callable

from pocketsphinx import Decoder

from mycroft.interfaces.speech.wake_word_engines.wake_word_engine_plugin import WakeWordEnginePlugin
from mycroft.util.misc import download_extract_tar


class PocketsphinxEngine(WakeWordEnginePlugin):
    # Padding of silence when feeding to pocketsphinx
    SILENCE_SEC = 0.01
    url = 'https://github.com/MatthewScholefield/pocketsphinx-models/raw/master/{lang}.tar.gz'

    def __init__(self, rt, on_activation: Callable):
        super().__init__(rt, on_activation)
        lang = rt.config['lang']
        self.hmm_folder = join(rt.paths.user_config, 'models', lang)
        self.rate, self.width = self.rec_config['sample_rate'], self.rec_config['sample_width']
        self.padding = b'\0' * int(self.rate * self.width * self.SILENCE_SEC)
        self.buffer = b''

        download_extract_tar(self.url.format(lang=lang), self.hmm_folder)

        config = Decoder.default_config()
        config.set_string('-hmm', self.hmm_folder)
        config.set_string('-dict', self._create_dict(self.wake_word, self.config['phonemes']))
        config.set_string('-keyphrase', self.wake_word)
        config.set_float('-kws_threshold', float(self.config['threshold']))
        config.set_float('-samprate', self.rate)
        config.set_int('-nfft', 2048)
        config.set_string('-logfn', '/dev/null')
        self.ps = Decoder(config)

    @staticmethod
    def _create_dict(key_phrase, phonemes):
        fd, file_name = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(key_phrase + ' ' + phonemes.replace(' . ', ' '))
        return file_name

    def _transcribe(self, raw_audio):
        self.ps.start_utt()
        self.ps.process_raw(raw_audio, False, False)
        self.ps.end_utt()
        return self.ps.hyp()

    def startup(self):
        self.buffer = b'\0' * int(self.width * self.rate * self.config['wake_word_length'])

    def shutdown(self):
        self.buffer = b''

    def pause_listening(self):
        pass

    def continue_listening(self):
        pass

    def update(self, raw_audio: bytes):
        self.buffer = self.buffer[len(raw_audio):] + raw_audio

        transcription = self._transcribe(self.buffer + self.padding)
        if transcription and self.wake_word in transcription.hypstr.lower():
            self.on_activation()
