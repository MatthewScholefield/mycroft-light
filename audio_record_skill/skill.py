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
# 'License'); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
from subprocess import Popen

from threading import Thread

from mycroft.skill import MycroftSkill
from mycroft.util.audio import play_wav


class AudioRecordSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('record.begin', self.record_begin)
        self.register_intent('record.end', self.record_end)
        self.register_intent('playback.begin', self.playback_begin)
        self.register_intent('playback.end', self.playback_end)
        self.create_alias('stop', 'record.end')
        self.create_alias('stop', 'playback.end')
        self.record_process = None
        self.playback_process = None
        self.manually_terminated = False

        self.rate = self.config['rate']
        self.channels = self.config['channels']
        self.file_path = self.config['filename']

    def end_process(self, process_attr):
        process = getattr(self, process_attr)
        if process.poll() is None:
            self.manually_terminated = True
            process.terminate()
            process.wait()
        setattr(self, process_attr, None)
        self.stop_running()

    def notify_end(self, process_att, name):
        def notify():
            self.manually_terminated = False

            getattr(self, process_att).wait()
            self.end_process(process_att)

            if not self.manually_terminated:
                self.trigger_action(name)

        Thread(target=notify, daemon=True).start()

    def check_already_started(self):
        if self.playback_process is not None:
            self.set_action('already.playing')
            return True
        if self.record_process is not None:
            self.set_action('already.recording')
            return True
        return False

    def record_begin(self, intent_match):
        if self.check_already_started():
            return 0.6

        try:
            duration = self.parser.duration(intent_match.matches.get('duration', ''))
            dur_flag = ['-d', str(duration)]
            self.add_result('duration', self.parser.duration_to_str(duration))
            self.add_result('duration_s', duration)
        except ValueError:
            dur_flag = []

        def callback():
            self.record_process = Popen(['arecord', '-q', '-r', str(self.rate), '-c', str(self.channels), self.file_path] + dur_flag)
            self.notify_end('record_process', 'record.end')
            self.start_running()

        self.set_callback(callback)

    def record_end(self):
        if self.record_process is None:
            self.set_action('no.recording.to.end')
            return 0.6

        self.set_callback(lambda: self.end_process('record_process'))
        return 0.88

    def playback_begin(self):
        if self.check_already_started():
            return 0.6

        def callback():
            self.playback_process = play_wav(self.file_path)
            self.notify_end('playback_process', 'playback.end')
            self.start_running()
        self.set_callback(callback)

    def playback_end(self):
        if self.playback_process is None:
            self.set_action('no.playback.to.end')
            return 0.6

        self.set_callback(lambda: self.end_process('playback_process'))
        return 0.8
