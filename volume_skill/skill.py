# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
from alsaaudio import Mixer

from mycroft.package_cls import Package
from mycroft.skill_plugin import intent_handler, intent_prehandler
from mycroft.util import log
from mycroft.util.audio import play_audio
from mycroft_core import MycroftSkill


class VolumeSkill(MycroftSkill):
    _config = {
        'min': 0,
        'max': 100,
        'steps': 11
    }
    _required_attributes = {
        'audio-output'
    }

    def __init__(self):
        super().__init__()
        self.min = self.config['min']
        self.max = self.config['max']
        self.steps = self.config['steps']
        self.change_volume_wav = self.filesystem.path('change_volume.wav')
        self.prev_volume = None
        self.register_entity('level')

    def get_level(self):
        return self.steps * (Mixer().getvolume()[0] - self.min) / (self.max - self.min)

    def change_volume(self, change):
        self.set_volume(self.get_level() + change)

    def set_volume(self, volume):
        volume = min(max(volume, 0), self.steps)
        Mixer().setvolume(round(100 * volume / self.steps))
        self.rt.interfaces.faceplate.command('eyes.volume={}'.format(round(volume)))
        play_audio(self.change_volume_wav)

    @intent_handler('increase.volume')
    def increase_volume(self):
        self.change_volume(+1)

    @intent_handler('decrease.volume')
    def decrease_volume(self):
        self.change_volume(-1)

    @intent_prehandler('set.volume')
    def handle_set_volume(self, p: Package):
        try:
            p.data['level'] = float(p.match['level'])
            return p.add(confidence=0.8)
        except (KeyError, ValueError):
            log.exception('Parsing Level')
            p.data['min'] = 0
            p.data['max'] = self.steps
            p.action = 'invalid.volume'
            return p.add(confidence=0.6)

    @handle_set_volume.handler
    def handle_set_volume(self, p: Package):
        if p.action == 'set.volume':
            self.set_volume(p.data['level'])

    @intent_prehandler('check.volume')
    def handle_check_volume(self, p: Package):
        p.data['volume'] = self.get_level()

    @intent_prehandler('mute.volume')
    def handle_mute(self, p: Package):
        p.faceplate.mouth.text = 'Volume Muted'
        p.faceplate.eyes.color = (185, 116, 116)
        return p.add(confidence=0.8 if self.get_level() != 0 else 0.6)

    @handle_mute.handler
    def handle_mute(self):
        self.prev_volume = self.get_level()
        self.set_volume(0)

    @intent_prehandler('unmute.volume')
    def handle_unmute(self, p: Package):
        return p.add(confidence=0.8 if self.get_level() == 0 else 0.5)

    @handle_unmute.handler
    def handle_unmute(self):
        self.set_volume(self.prev_volume)