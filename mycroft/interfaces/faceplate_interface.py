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
from threading import Thread
from time import monotonic

import serial
from os.path import isfile

from mycroft.interfaces.interface_plugin import InterfacePlugin
from mycroft.package_cls import Package
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


class FaceplateInterface(InterfacePlugin):
    """Interact with Mycroft via the Mark 1 Enclosure"""
    _package_struct = {
        'faceplate': {
            'mouth': {
                'text': str,
                'reset': (),
                'listen': ()
            },
            'eyes': {
                'blink': (),
                'reset': (),
                'color': (int, int, int)
            }
        }
    }

    def __init__(self, rt):
        super().__init__(rt)
        if not isfile(self.config['url']):
            raise NotImplementedError

        self.serial = serial.serial_for_url(url=self.config['url'], baudrate=self.config['rate'],
                                            timeout=self.config['timeout'])
        self.queue = Queue()
        self.timers = []

    def run(self):
        Thread(target=self._run_serial, daemon=True).start()
        while self.rt.main_thread:
            line = self.serial.readline().decode()
            if 'volume.up' in line:
                self.rt.skills.volume.increase_volume()
            elif 'volume.down' in line:
                self.rt.skills.volume.decrease_volume()
            elif 'Command: ' in line:
                pass  # Reply from Arduino
            elif len(line.strip()) > 0:
                log.warning('Could not handle message: ' + line)

    def _run_serial(self):
        while self.rt.main_thread:
            command = self.queue.get()
            if 'viseme' not in command:
                log.debug('Sending faceplate command:', command)
            self.serial.write((command + '\n').encode())
            self.queue.task_done()

    def command(self, message):
        self.queue.put(message.strip())

    def visemes(self, dur_str):
        begin_time = monotonic()
        for dur_cmd in dur_str.split(' '):
            parts = dur_cmd.split(':')
            if len(parts) != 2:
                log.error('Invalid .dur line:' + dur_cmd)

            phoneme, desired_delta = parts[0], float(parts[1])

            self.viseme(phoneme)

            cur_delta = monotonic() - begin_time
            sleep_time = desired_delta - cur_delta
            if sleep_time > 0:
                sleep_time(sleep_time)

    def execute(self, p: Package):
        handlers = {
            'faceplate': {
                'eyes': {
                    'blink': self.blink,
                    'color': self.eye_color,
                    'reset': self.reset_eyes
                },
                'mouth': {
                    'text': self.text,
                    'reset': self.reset_mouth,
                    'listen': self.listen
                }
            }
        }

        p.execute(handlers)

    ################################

    def listen(self):
        self.command('mouth.listen')

    def viseme(self, phone):
        self.command('mouth.viseme=' + VISEMES.get(phone, 4))

    def blink(self):
        self.command('eyes.blink')

    def eye_color(self, color: tuple):
        r, g, b = color
        self.command('eyes.color=' + str(r << 16 + g << 8 + b))

    def reset_mouth(self):
        self.command('mouth.reset')

    def reset_eyes(self):
        self.command('eyes.reset')

    def text(self, text):
        self.command('mouth.text=' + text)

    def reset(self):
        self.reset_mouth()
        self.reset_eyes()
        self.eye_color((0, 255, 255))
