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
from time import sleep

import psutil
from difflib import SequenceMatcher
from psutil import Process
from typing import Tuple, Optional

from mycroft_core import MycroftSkill, Package, intent_prehandler


class SystemStatusSkill(MycroftSkill):
    def __init__(self):
        super().__init__()

        def mkmethod(i):
            return lambda self, p: self.add_memory_result(p, i, getattr(psutil.virtual_memory(), i))

        for i in ['free', 'used', 'total']:
            self.register_intent(mkmethod(i), 'mem.' + i)

    @staticmethod
    def format_kb(amount):
        gb = amount / (1024 * 1024 * 1024)
        if gb > 1.0:
            return round(gb, 1), 'GB', 'Gigabytes'
        else:
            return round(gb * 1024), 'MB', 'Megabytes'

    def add_memory_result(self, p: Package, prefix, bytes):
        num, short, long = self.format_kb(bytes)
        p.data[prefix + '_short'] = str(num) + ' ' + short
        p.data[prefix + '_long'] = str(num) + ' ' + long

    @intent_prehandler('cpu.total.usage')
    def total_cpu(self, p: Package):
        p.data['percent'] = psutil.cpu_percent(0.2) / psutil.cpu_count()

    @intent_prehandler('mem.max.process')
    def max_mem(self, p: Package):
        proc = max(list(psutil.process_iter()), key=lambda x: x.memory_info_ex()[0])

        p.data['name'] = proc.name()
        p.data['command'] = ' '.join(proc.cmdline())
        p.data['percent'] = proc.memory_percent()
        self.add_memory_result(p, 'used', proc.memory_info_ex()[0])

    @staticmethod
    def find_process(name) -> Tuple[float, Optional[Process]]:
        """Returns confidence, process"""
        name = name.lower()
        for i in psutil.process_iter():
            proc_name = i.name().lower().replace('-', ' ')
            if proc_name in name or name in proc_name:
                return SequenceMatcher(name, proc_name).ratio(), i
        return 0.0, None

    @intent_prehandler('mem.usage.application')
    def app_mem(self, p: Package):
        conf, proc = self.find_process(p.match['application'])
        if proc:
            p.data['name'] = proc.name()
            p.data['command'] = ' '.join(proc.cmdline())
            self.add_memory_result(p, 'used', proc.memory_info_ex()[0])
        else:
            p.data['app'] = p.match['application']
            p.action = 'app.not.found'
        return proc.add(confidence=0.6 + 0.4 * conf)

    @intent_prehandler('cpu.max.process')
    def max_cpu(self, p: Package):
        processes = list(psutil.process_iter())
        for i in processes:
            i.cpu_percent()
        sleep(0.2)
        usages = [i.cpu_percent() / psutil.cpu_count() for i in processes]
        percent = max(usages)
        name = processes[usages.index(percent)].name()

        p.data['name'] = name
        p.data['percent'] = percent

    @intent_prehandler('kill.process')
    def kill_process(self, p: Package):
        conf, proc = self.find_process(p.match['application'])
        if not proc:
            return p.add(confidence=0.0)
        return p.add(confidence=0.4 + 0.6 * conf, data={'name': proc.name(), 'proc': proc})

    @kill_process.handler
    def kill_process(self, p: Package):
        if self.confirm('confirm.kill', p):
            p.data['proc'].terminate()
            return p.add(action='kill.complete')
        else:
            return p.add(action='canceled')

    @intent_prehandler('cpu.usage.application')
    def app_cpu(self, p: Package):
        conf, proc = self.find_process(p.match['application'])
        if proc:
            p.data['name'] = proc.name()
            p.data['command'] = ' '.join(proc.cmdline())
            p.data['percent'] = proc.cpu_percent(0.2) / psutil.cpu_count()
        else:
            p.data['app'] = p.match['application']
            p.action = 'app.not.found'
        return p.add(confidence=0.6 + 0.4 * conf)
