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
import sys

import pydora.player
from pandora import clientbuilder
from pydora.audio_backend import VLCPlayer, PlayerUnusable, MPG123Player, \
    UnsupportedEncoding
from threading import Thread, Event

from mycroft.skill import MycroftSkill


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
        self.create_alias('stop', 'pandora.stop')

    def create_player(self):
        try:
            return VLCPlayer(self, sys.stdin)
        except PlayerUnusable:
            return MPG123Player(self, sys.stdin)

    def start_playing(self):
        """Blocking"""
        for song in self.stations[0].get_playlist():
            try:
                self.player.play(song)
            except StopIteration:
                return

    def play_forever(self):
        while True:
            try:
                self.player.play_station(self.stations[0])
            except UnsupportedEncoding:
                pass

    def handle_play(self):
        def callback():
            Thread(target=self.play_forever, daemon=True).start()
            self.player.start()
            self.start_running()
            self.set_action('')
        self.set_callback(callback)
        return 0.6 if self.is_running() else 0.9

    def handle_pause(self):
        self.set_callback(self.player.pause)
        return 0.9 if self.is_running() else 0.6

    def handle_next(self):
        self.set_callback(self.player.stop)
        return 0.9 if self.is_running() else 0.6

    def handle_stop(self):
        def callback():
            self.player.end_station()
            self.stop_running()
        self.set_callback(callback)
        return 0.9 if self.is_running() else 0.6

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
        pass

    def post_poll(self):
        pass

    def input(self, value, song):
        pass
