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
from os.path import isdir, isfile, join

from pocketsphinx import Decoder

from mycroft.frontends.speech.recognizers.recognizer_plugin import RecognizerPlugin


def download_model(lang, paths):
    model_folder = join(paths.user_config, 'model')
    model_en_folder = join(model_folder, lang)

    if not isdir(model_folder):
        mkdir(model_folder)
    if not isdir(model_en_folder):
        mkdir(model_en_folder)
        file_name = paths.model_dir + '.tar.gz'
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


class PocketsphinxRecognizer(RecognizerPlugin):
    # Padding of silence when feeding to pocketsphinx
    SILENCE_SEC = 0.01

    def __init__(self, rt):
        super().__init__(rt)

        self.lang = rt.config['lang']
        download_model(self.lang, rt.paths)

        self.key_phrase = self.listener_config['wake_word'].replace(' ', '-')
        self.threshold = self.config['threshold']
        self.phonemes = self.config['phonemes']
        self.decoder = Decoder(self.create_config(rt.paths, self.create_dict()))

        self.padding = b'\0' * int(self.sample_rate * self.sample_width * self.SILENCE_SEC)

    def create_dict(self):
        (fd, file_name) = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(self.key_phrase + ' ' + self.phonemes.replace(' . ', ' '))
        return file_name

    def create_config(self, paths, dict_name):
        config = Decoder.default_config()
        config.set_string('-hmm', join(paths.user_config, 'model'))
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
