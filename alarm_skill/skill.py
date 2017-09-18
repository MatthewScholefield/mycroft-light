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
from datetime import datetime
from time import time as get_time
from time import mktime

import json
from parsedatetime import Calendar
from threading import Timer

from mycroft import MycroftSkill
from mycroft.util import LOG


class AlarmSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('alarm.list', self.list_alarms)
        self.register_intent('alarm.set', self.set_alarm)
        self.register_intent('alarm.remove', self.remove_alarm)
        self.register_intent('alarm.stop', self.stop_alarm)
        self.create_alias('stop', 'alarm.stop')
        self.data_name = 'alarms.json'
        self.calendar = Calendar()
        self.notify_delay = self.config['notify_delay']
        self.alarm_is_active = False
        self.alarm_cancelled = False

        if not self.is_file(self.data_name):
            self.alarms = []
            self.save_alarms()
        else:
            self.alarms = self.load_alarms()

        self.create_timers()

    def load_alarms(self):
        return json.load(self.open_file(self.data_name))

    def save_alarms(self):
        self.alarms = [alarm for alarm in self.alarms if alarm['time'] > get_time()]

        with self.open_file(self.data_name, 'w') as f:
            f.write(json.dumps(self.alarms, indent=4, sort_keys=True))

    def create_timer_thread(self, delay, label):
        t = Timer(interval=delay, function=self.trigger_alarm, args=(label,))
        t.daemon = True
        t.start()

    def trigger_alarm(self, label):
        if self.alarm_cancelled:
            self.alarm_cancelled = False
            return

        self.alarm_is_active = True
        if label != '':
            self.add_result('label', label)
        self.trigger_action('alarm.notify')
        self.create_timer_thread(self.notify_delay, label)

    def create_timer(self, alarm):
        time = alarm['time']
        label = alarm['label']
        self.create_timer_thread(time - get_time(), label)

    def create_timers(self):
        for alarm in self.alarms:
            self.create_timer(alarm)

    def list_alarms(self):
        if len(self.alarms) == 0:
            self.set_action('no.alarms')
            return 0.7
        alarm_str = ''
        join_str = ', '
        for alarm in self.alarms:
            dt = datetime.fromtimestamp(alarm['time'])
            alarm_str += dt.strftime('%I:%M %p %A')
            if alarm['label'] != '':
                alarm_str += ': ' + alarm['label']
            alarm_str += join_str
        alarm_str = alarm_str[:-len(join_str)]
        self.add_result('alarms', alarm_str)
        return 0.8

    def set_alarm(self, intent_match):
        label = intent_match.matches.get('action', '')
        if label != '':
            self.add_result('label', label)

        t, code = self.calendar.parse(intent_match.query)
        if code == 0:
            self.set_action('no.time')
            return 0.6

        since_epoch = mktime(t)
        dt = datetime.fromtimestamp(since_epoch)
        if since_epoch <= get_time():
            self.set_action('time.in.past')
            return 0.6

        formats = [
            ('day', '%d'),
            ('weekday', '%A'),
            ('weekday_num', '%w'),
            ('month', '%B'),
            ('month_num', '%m'),
            ('year_short', '%y'),
            ('year', '%Y'),
            ('hour', '%I'),
            ('am_pm', '%p'),
            ('minute', '%M')
        ]

        for key, fmt in formats:
            LOG.debug('Key: ' + key + ', value: ' + dt.strftime(fmt))
            self.add_result(key, dt.strftime(fmt))

        def callback():
            alarm = {
                'time': since_epoch,
                'label': label
            }
            self.create_timer(alarm)
            self.alarms.append(alarm)
            self.save_alarms()

        self.set_callback(callback)

        return 0.8

    def remove_alarm(self):
        def callback():
            self.alarms.clear()
            self.save_alarms()
        self.set_callback(callback)
        if len(self.alarms) > 0:
            return 0.8
        else:
            self.set_action('none.to.remove')
            return 0.6

    def stop_alarm(self):
        def callback():
            self.alarm_cancelled = True
            self.alarm_is_active = False
            self.save_alarms()
        self.set_callback(callback)

        if self.alarm_is_active:
            return 0.9
        else:
            self.set_action('none.to.stop')
            return 0.6