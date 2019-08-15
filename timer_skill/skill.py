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
import time
from collections import namedtuple

from mycroft.skill_plugin import with_entity, intent_prehandler
from mycroft_core import MycroftSkill, Package, intent_handler

Alarm = namedtuple('Alarm', 'time name')


class TimerSkill(MycroftSkill):
    NOTIFY_DELAY = 10

    def __init__(self):
        super().__init__()
        self.alarms = self.load()
        self.units = self.locale('units.txt')
        self.alarm_timers = []
        self.notifiers = {}
        self.reschedule()

    def reschedule(self):
        self.unschedule()
        self.alarm_timers = [
            self.schedule_once(self.notify, delay=alarm.time - time.time(), args=[alarm])
            for alarm in self.alarms
        ]

    def unschedule(self):
        for i in self.alarm_timers:
            self.cancel_task(i)

    def shutdown(self):
        self.unschedule()

    def load(self):
        return [Alarm(*i) for i in self.filesystem.read('alarms.json').list()]

    def save(self):
        self.filesystem.write('alarms.json').list([[i.time, i.name] for i in self.alarms])

    def notify(self, alarm: Alarm):
        self.execute(self.package(action='alarm.notify', data=dict(
            name=alarm.name,
        )))
        self.notifiers[alarm] = self.schedule_once(self.notify, self.NOTIFY_DELAY, args=[alarm])

    @intent_prehandler('stop')
    def stop(self, p: Package):
        if self.notifiers:
            return p.add(confidence=0.8)
        return p.add(confidence=0.0)

    @stop.handler
    def stop(self):
        for alarm, task in self.notifiers.items():
            self.cancel_task(task)
            if alarm in self.alarms:
                self.alarms.remove(alarm)
        self.notifiers = {}
        self.save()

    def find_unit_seconds(self, unit_str):
        for unit, value in zip(self.units, [1, 60, 60 * 60]):
            if unit in unit_str:
                return value
        raise ValueError(unit_str)

    @with_entity('unit')
    @with_entity('number')
    @with_entity('timer_type')
    @intent_handler('set.timer')
    def handle_set_timer(self, p: Package):
        name = p.match.get('timer_type', p.match.get('timer_label'))
        timer_delta = int(p.match['number']) * self.find_unit_seconds(p.match['unit'])

        self.alarms.append(Alarm(time=time.time() + timer_delta, name=name))
        self.reschedule()
        self.save()

        p.data = {
            'number': p.match['number'],
            'unit': p.match['unit'],
            'name': name
        }

    @intent_prehandler('list.timers')
    def handle_list_timers(self, p: Package):
        p.data = {
            'timers': [
                self.dialog(
                    'timer_list', type=alarm.name,
                    duration=self.dialog('duration', minutes=int(alarm.time - time.time()) // 60)
                )
                for alarm in self.alarms
            ]
        }
