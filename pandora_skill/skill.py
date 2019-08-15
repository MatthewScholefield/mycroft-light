# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
#
# This file is part of Mycroft Simple
# (see https://github.com/MatthewScholefield/mycroft-simple).
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
from builtins import StopIteration
from io import StringIO

from pandora import clientbuilder
from pydora.audio_backend import VLCPlayer, PlayerUnusable, MPG123Player, \
    UnsupportedEncoding

from pydora.utils import iterate_forever

from mycroft_core import MycroftSkill

from mycroft.package_cls import Package
from mycroft.skill_plugin import intent_handler, intent_prehandler
from mycroft.util import log


class PandoraSkill(MycroftSkill):
    _config = {
        'pandora_conf': '~/.mycroft/pandora.conf'
    }
    _required_attributes = ['audio-output']

    def __init__(self):
        super().__init__()
        self.active = False
        self.must_stop = False
        self.player = self.create_player()
        builder = clientbuilder.PydoraConfigFileBuilder(os.path.expanduser(self.config['pandora_conf']))
        self.client = builder.build()

        self.stations = self.client.get_station_list()

    def create_player(self):
        dummy_stdin = StringIO()
        dummy_stdin.fileno = lambda: 0
        try:
            return VLCPlayer(self, dummy_stdin)
        except PlayerUnusable:
            log.warning('Unable to find VLC. MPG123 won\'t work for most songs')
            return MPG123Player(self, dummy_stdin)

    def start_playing(self, index):
        """Blocking"""
        for song in iterate_forever(self.stations[index].get_playlist):
            try:
                self.player.play(song)
            except UnsupportedEncoding:
                log.warning('Unsupported encoding')
            except StopIteration:
                log.info('Stopping Pandora...')
                self.player.stop()
                return

    def play_forever(self, index):
        self.start_playing(index)

    @intent_prehandler('play')
    @intent_prehandler('music.play')
    @intent_prehandler('pandora.play')
    def handle_play(self, p: Package):
        p.action = ''
        if 'id' in p.match:
            p.action = 'pandora.start.station'
            p.data['id'] = p.match['id']

        if self.active:
            return p.add(confidence=0.6)

    @handle_play.handler
    def handle_play(self, p: Package):
        p.action = 'pandora.play'
        if self.active:
            self.player.pause()
        else:
            self.player.start()
            self.active = True
            self.create_thread(self.play_forever, int(p.match.get('id', 0)))

    @intent_prehandler('pause')
    @intent_prehandler('music.pause')
    @intent_prehandler('pandora.pause')
    def handle_pause(self, p: Package):
        print('PAUSE PREHANDLER')
        return p.add(confidence=0.8 if self.active else 0.4)

    @handle_pause.handler
    def handle_pause(self):
        print('PAUSE HANDLER')
        self.player.pause()

    @intent_prehandler('music.next')
    @intent_prehandler('pandora.next')
    def handle_next(self, p: Package):

        return p.add(confidence=0.8 if self.active else 0.4)

    @handle_next.handler
    def handle_next(self):
        self.player.stop()

    @intent_handler('stop')
    @intent_handler('music.stop')
    @intent_handler('pandora.stop')
    def handle_stop(self, p: Package):
        return p.add(confidence=0.8 if self.active else 0.3)

    @handle_stop.handler
    def handle_stop(self):
        self.must_stop = True

    # === Pandora API Callbacks ===
    def play(self, song):
        if song.is_ad:
            self.execute(self.package(action='ad'))
            return
        self.execute(self.package(action='pandora.play', data=dict(
            song=song.song_name, artist=song.artist_name
        )))

    def pre_poll(self):
        if self.must_stop:
            self.must_stop = False
            self.active = False
            raise StopIteration

    def post_poll(self):
        pass

    def input(self, value, song):
        pass

    def shutdown(self):
        self.must_stop = True
