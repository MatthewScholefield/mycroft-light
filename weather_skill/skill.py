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
from typing import List, TYPE_CHECKING
from .mycroft_owm import MycroftOWM

if TYPE_CHECKING:  # noqa
    from pyowm.webapi25.weather import Weather

from mycroft_core import MycroftSkill, intent_handler, Package, intent_prehandler
from mycroft.intent_match import MissingIntentMatch


class WeatherSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.owm = MycroftOWM(self.rt)
        coord_conf = self.rt.config['location']['coordinate']
        self.coord = (coord_conf['latitude'], coord_conf['longitude'])

    def get_weathers(self):
        return self.owm.daily_forecast_at_coords(*self.coord).get_forecast().get_weathers()

    @intent_handler('weather')
    def weather(self, p: Package):
        weather = self.get_weathers()[0]  # type: Weather
        temp_unit = self.rt.config['locale']['temperature']
        temp = weather.get_temperature('celsius' if temp_unit == 'c' else 'fahrenheit')

        p.data.update({
            'condition': weather.get_status().lower(),
            'temp_day': int(temp['day']),
            'temp_max': int(temp['max']),
            'temp_min': int(temp['min'])
        })

    def when_condition(self, condition_name):
        from pyowm.webapi25 import weatherutils
        from pyowm.webapi25.configuration25 import weather_code_registry
        return weatherutils.filter_by_status(
            self.get_weathers(), condition_name, weather_code_registry
        )

    @intent_prehandler('when.will.condition')
    def when_will_condition(self, p: Package):
        cond = p.match['condition']
        if cond not in {'rain', 'sun', 'fog', 'snow',  'storm', 'hurricane', 'tornado'}:
            raise MissingIntentMatch('condition')
        p.data['condition'] = p.match['condition']

        cond_days = self.when_condition(cond)  # type: List[Weather]

        if len(cond_days) > 0:
            next_rain_day = cond_days[0]
            date = next_rain_day.get_reference_time('date')
            p.data.update({
                'weekday': date.strftime('%A')
            })
