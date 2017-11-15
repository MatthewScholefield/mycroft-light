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
from abc import ABCMeta, abstractmethod

from subprocess import Popen


class MycroftTTS(metaclass=ABCMeta):
    def __init__(self, path_manager, formats):
        self.path_manager = path_manager
        self.formats = formats

    def speak_wav(self, file_name, phonemes=''):
        p = Popen(self.path_manager.play_wav_cmd(file_name).split(' '))
        self.formats.faceplate.visemes(phonemes)
        p.wait()

    @abstractmethod
    def speak(self, text):
        """Blocking method that speaks a message"""
        pass
