from typing import List

from pyowm.webapi25 import weatherutils
from pyowm.webapi25.configuration25 import weather_code_registry
from pyowm.webapi25.weather import Weather

from mycroft_core import MycroftSkill, intent_handler, Package, intent_prehandler
from mycroft.intent_match import MissingIntentMatch


class WeatherSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        from pyowm import OWM
        key = self.rt.remote_key.create_key('api.openweathermap.org', 'weather')
        self.owm = OWM(key)
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
        return weatherutils.filter_by_status(
            self.get_weathers(), condition_name, weather_code_registry
        )

    @intent_prehandler('when.will.condition')
    def when_will_condition(self, p: Package):
        cond = p.match['condition']
        if cond not in {'rain', 'sun', 'fog', 'snow',  'storn', 'hurricane', 'tornado'}:
            raise MissingIntentMatch('condition')
        p.data['condition'] = p.match['condition']

        cond_days = self.when_condition(cond)  # type: List[Weather]

        if len(cond_days) > 0:
            next_rain_day = cond_days[0]
            date = next_rain_day.get_reference_time('date')
            p.data.update({
                'weekday': date.strftime('%A')
            })
