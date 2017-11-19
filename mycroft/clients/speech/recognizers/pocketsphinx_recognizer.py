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
from os import mkdir
from os.path import isdir, isfile

from pocketsphinx import Decoder

from mycroft.clients.speech.recognizers.wake_word_recognizer import MycroftListener


def download_model(lang, path_manager):
    model_folder = path_manager.model_dir_no_lang
    model_en_folder = path_manager.model_dir

    if not isdir(model_folder):
        mkdir(model_folder)
    if not isdir(model_en_folder):
        mkdir(model_en_folder)
        file_name = path_manager.model_dir + '.tar.gz'
        if not isfile(file_name):
            import urllib.request
            import shutil
            url = 'https://github.com/MatthewScholefield/pocketsphinx-models/raw/master/' + lang + '.tar.gz'
            with urllib.request.urlopen(url) as response, open(file_name, 'wb') as file:
                shutil.copyfileobj(response, file)

        import tarfile
        tar = tarfile.open(file_name)
        tar.extractall(path=model_en_folder)
        tar.close()


class PocketsphinxListener(MycroftListener):
    # Padding of silence when feeding to pocketsphinx
    SILENCE_SEC = 0.01

    def __init__(self, path_manager, global_config):
        super().__init__(global_config)

        self.lang = global_config.get('lang')
        download_model(self.lang, path_manager)

        self.key_phrase = self.config.get('wake_word').replace(' ', '-')
        self.threshold = self.config.get('threshold')
        self.phonemes = self.config.get('phonemes')
        self.decoder = Decoder(self.create_config(path_manager, self.create_dict()))

        self.padding = b'\0' * int(self.sample_rate * self.sample_width * self.SILENCE_SEC)

    def create_dict(self):
        (fd, file_name) = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(self.key_phrase + ' ' + self.phonemes.replace(' . ', ' '))
        return file_name

    def create_config(self, path_manager, dict_name):
        config = Decoder.default_config()
        config.set_string('-hmm', path_manager.model_dir)
        config.set_string('-dict', dict_name)
        config.set_string('-keyphrase', self.key_phrase)
        config.set_float('-kws_threshold', float(self.threshold))
        config.set_float('-samprate', self.sample_rate)
        config.set_int('-nfft', 2048)
        config.set_string('-logfn', '/dev/null')
        return config

    def transcribe(self, raw_audio):
        self.decoder.start_utt()
        self.decoder.process_raw(raw_audio, False, False)
        self.decoder.end_utt()
        return self.decoder.hyp()

    def found_wake_word(self, raw_audio):
        transcription = self.transcribe(raw_audio + self.padding)
        return transcription and self.key_phrase in transcription.hypstr.lower()
