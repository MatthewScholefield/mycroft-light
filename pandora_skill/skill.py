#
# Copyright (c) 2017 Mycroft AI, Inc.
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
#
import os
from builtins import StopIteration
from io import StringIO

from pandora import clientbuilder
from pydora.audio_backend import VLCPlayer, PlayerUnusable, MPG123Player, \
    UnsupportedEncoding
from threading import Thread

from pydora.utils import iterate_forever

from mycroft import MycroftSkill
from twiggy import log


class PandoraSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.player = self.create_player()

        builder = clientbuilder.PydoraConfigFileBuilder(os.path.expanduser(self.config['pandora_conf']))
        self.client = builder.build()
        self.stations = self.client.get_station_list()
        self.register_intent('pandora.play', self.handle_play)
        self.register_intent('pandora.pause', self.handle_pause)
        self.register_intent('pandora.stop', self.handle_stop)
        self.register_intent('pandora.next', self.handle_next)
        self.create_alias('music.play', 'pandora.play')
        self.create_alias('music.pause', 'pandora.pause')
        self.create_alias('music.stop', 'pandora.stop')
        self.create_alias('music.next', 'pandora.next')
        self.create_alias('pause', 'pandora.pause')
        self.create_alias('play', 'pandora.play')
        self.create_alias('stop', 'pandora.stop')
        self.set_av_run_time(3 * 60)
        self.must_stop = False

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

    def handle_play(self, intent_match):
        def callback():
            if self.is_running():
                self.player.pause()
            else:
                self.player.start()
                self.start_running()
                self.create_thread(self.play_forever, args=(int(intent_match.matches.get('id', 0)),))

        self.set_action('')
        if 'id' in intent_match.matches:
            self.set_action('pandora.start.station')
            self.add_result('id', intent_match.matches['id'])

        self.set_callback(callback)
        if self.is_running():
            return 0.6

    def handle_pause(self):
        self.set_callback(self.player.pause)

    def handle_next(self):
        self.set_callback(self.player.stop)

    def handle_stop(self):
        def callback():
            self.must_stop = True
        self.set_callback(callback)

    # Pandora API Callbacks
    def play(self, song):
        def callback():
            if song.is_ad:
                self.set_action('ad')
                return
            self.add_result('song', song.song_name)
            self.add_result('artist', song.artist_name)
        self.trigger_action('pandora.play', callback)

    def pre_poll(self):
        if self.must_stop:
            self.must_stop = False
            self.stop_running()
            raise StopIteration

    def post_poll(self):
        pass

    def input(self, value, song):
        pass
