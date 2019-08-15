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
import re
from glob import glob
from mycroft_core import MycroftSkill, Package, intent_handler
from random import shuffle
from subprocess import TimeoutExpired, Popen
from typing import Tuple, Iterator

from mycroft.skill_plugin import intent_prehandler
from mycroft.util.text import find_match


class DesktopLauncherSkill(MycroftSkill):
    valid_command_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_0123456789 %'
    _required_attributes = ['desktop-interface']

    def __init__(self):
        super().__init__()
        self.name_to_cmd = {
            name: re.sub('%[fFuUdDnNickvm]', '', cmd) for cmd, name in self.find_apps()
        }
        self.name_to_cmd.update({cmd.split()[0]: cmd for cmd in self.name_to_cmd.values()})

    @classmethod
    def norm(cls, s):
        return ''.join(c for c in s.strip() if c in cls.valid_command_chars)

    def find_apps(self) -> Iterator[Tuple[str, str]]:
        for desktop_file in glob('/usr/share/applications/*.desktop'):
            cmd = name = ''
            with open(desktop_file) as f:
                for line in f:
                    if line.startswith('Exec='):
                        cmd = self.norm(line[len('Exec='):])
                    elif line.startswith('Name='):
                        name = self.norm(line[len('Name='):])
                    if name and cmd:
                        break
            if cmd and name:
                yield cmd, name

    @intent_prehandler('launch.app')
    def launch_app(self, p: Package):
        app, conf = find_match(p.match['app'], self.name_to_cmd)
        if conf < 0.6:
            return p.add(confidence=0.0)

        p.data = {
            'app': app,
            'cmd': self.name_to_cmd[app]
        }

    @launch_app.handler
    def launch_app(self, p: Package):
        try:
            code = Popen(p.data['cmd'].split()).wait(0.1)
        except TimeoutExpired:
            return
        else:
            p.data.update({'code': code})
            if code == 0:
                p.action = 'command.successful'
            else:
                p.action = 'command.failed'

    @intent_handler('what.can.i.launch')
    def what_can_i_launch(self, p: Package):
        names = list(self.name_to_cmd)
        shuffle(names)
        p.data = {
            'apps': names[:5]
        }
