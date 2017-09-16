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
import pytz
from geopy import geocoders
from datetime import datetime
from mycroft import MycroftSkill


class TimeSkill(MycroftSkill):
    fmt = '%l:%M %p'

    def __init__(self):
        super().__init__()
        self.register_intent('time', self.time)
        self.register_intent('date', self.date)
        self.suffixes = ['th', 'st', 'nd', 'rd'] + ['th'] * 6

    def _get_suffix(self, n):
        if int(n / 10) % 10 == 1:
            return 'th'
        return self.suffixes[n % 10]

    def get_cur_time(self, tz):
        return datetime.now(pytz.timezone(tz)).strftime(self.fmt)

    def get_tz(self, location_str):
        g = geocoders.GoogleV3()
        code = g.geocode(location_str)
        return code.address, str(g.timezone(code.point))

    def time(self, intent_match):
        if 'place' in intent_match.matches:
            place = intent_match.matches['place']
            try:
                address, tz = self.get_tz(place)
                self.add_result('place', place if place.lower() in address.lower() else address)
            except AttributeError:
                self.set_action('no.timezone')
                self.add_result('place', place)
                return 0.6
        else:
            tz = self.global_config['location']['timezone']['code']

        self.add_result('time', self.get_cur_time(tz))

    def date(self):
        date = datetime.today()

        self.add_result('day', date.day)
        self.add_result('day_suffix', self._get_suffix(date.day))
        self.add_result('month', date.strftime('%B'))
        self.add_result('year', date.year)
        self.add_result('date_dot', str(date.day) + '.' + str(date.month) + '.' + str(date.year)[2:])
