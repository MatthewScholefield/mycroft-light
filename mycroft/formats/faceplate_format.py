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

from queue import Queue
from threading import Timer
from time import sleep, time as get_time

import serial

from mycroft.formats.format_plugin import FormatPlugin
from mycroft.util import log

VISEMES = {
    # /A group
    'v': '5',
    'f': '5',
    # /B group
    'uh': '2',
    'w': '2',
    'uw': '2',
    'er': '2',
    'r': '2',
    'ow': '2',
    # /C group
    'b': '4',
    'p': '4',
    'm': '4',
    # /D group
    'aw': '1',
    # /E group
    'th': '3',
    'dh': '3',
    # /F group
    'zh': '3',
    'ch': '3',
    'sh': '3',
    'jh': '3',
    # /G group
    'oy': '6',
    'ao': '6',
    # /Hgroup
    'z': '3',
    's': '3',
    # /I group
    'ae': '0',
    'eh': '0',
    'ey': '0',
    'ah': '0',
    'ih': '0',
    'y': '0',
    'iy': '0',
    'aa': '0',
    'ay': '0',
    'ax': '0',
    'hh': '0',
    # /J group
    'n': '3',
    't': '3',
    'd': '3',
    'l': '3',
    # /K group
    'g': '3',
    'ng': '3',
    'k': '3',
    # blank mouth
    'pau': '4',
}


class FaceplateFormat(FormatPlugin):
    """Format data into sentences"""

    def __init__(self, rt):
        super().__init__(rt, '.faceplate')
        enc_cfg = self.rt.config['enclosure']
        self.serial = serial.serial_for_url(url=enc_cfg['port'], baudrate=enc_cfg['rate'],
                                            timeout=enc_cfg['timeout'])
        self.queue = Queue()
        self.timers = []

    def reset(self):
        self.command('mouth.reset')
        self.command('eyes.reset')
        self.command('eyes.color=65535')
        for i in self.timers:
            i.cancel()
        self.timers.clear()

    def visemes(self, dur_str):
        begin_time = get_time()
        for dur_cmd in dur_str.split(' '):
            parts = dur_cmd.split(':')
            if len(parts) != 2:
                continue

            phoneme = parts[0]
            desired_delta = float(parts[1])

            self.command('mouth.viseme=' + VISEMES.get(phoneme, 4))

            cur_delta = get_time() - begin_time
            sleep_time = desired_delta - cur_delta
            if sleep_time > 0:
                sleep(sleep_time)

    def run(self):
        while True:
            command = self.queue.get()
            if 'viseme' not in command:
                log.debug('Sending message:', command)
            self.serial.write((command + '\n').encode())
            self.queue.task_done()

    def command(self, message):
        self.queue.put(message.strip())

    def readline(self):
        return self.serial.readline().decode()

    def _add_timer(self, delay, fn):
        self.timers.append(Timer(delay, fn))
        self.timers[-1].start()

    def _run_repeat(self, serial_cmd, delay):
        self.command(serial_cmd)
        self._add_timer(delay, lambda: self._run_repeat(serial_cmd, delay))

    def _run_line(self, line):
        if line[0] == ':':
            custom_cmd, serial_cmd = list(filter(bool, line.split(':', 2)))
            split = custom_cmd.split()
            cmd, args = split[0], split[1:]

            def params(expected, default=0):
                ps = [float(i) for i in (args + [default] * (expected - len(args)))]
                return ps[0] if len(ps) == 1 else ps

            if cmd == 'repeat':
                delay, offset = params(2)
                self._add_timer(delay + offset, lambda: self._run_repeat(serial_cmd, delay))
            elif cmd == 'delay':
                self._add_timer(params(1), lambda: self.command(serial_cmd))
            else:
                raise ValueError('Unknown custom command: ' + custom_cmd)
        else:
            self.command(line)

    def generate_format(self, file, data):
        for line in file.readlines():
            for key, val in data.items():
                line = line.replace('{' + key + '}', val)
            line = line.strip()
            if len(line) != 0 and '{' not in line and '}' not in line:
                self._run_line(line)
