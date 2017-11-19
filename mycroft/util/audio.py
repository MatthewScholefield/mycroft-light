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

from subprocess import Popen, PIPE

from mycroft.configuration import ConfigurationManager


def play_wav(file_name):
    cmd = ConfigurationManager.get().get('play_wav_cmdline').replace('%1', file_name)
    return Popen(cmd.split(), stdout=PIPE, stderr=PIPE)


def play_mp3(file_name):
    cmd = ConfigurationManager.get().get('play_mp3_cmdline').replace('%1', file_name)
    return Popen(cmd.split(), stdout=PIPE, stderr=PIPE)


def play_audio(file_name):
    ext = file_name.split('.')[-1]
    if ext == 'wav':
        return play_wav(file_name)
    elif ext == 'mp3':
        return play_mp3(file_name)
    else:
        raise ValueError('Unknown Extension: ' + ext)
