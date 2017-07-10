import math
from multi_key_dict import multi_key_dict
from requests import HTTPError

from mycroft.api import Api
from pyowm import OWM
from pyowm.webapi25.forecaster import Forecaster
from pyowm.webapi25.forecastparser import ForecastParser
from pyowm.webapi25.observationparser import ObservationParser

from mycroft.skill import MycroftSkill
from mycroft.util import logger


class OWMApi(Api):
    def __init__(self):
        super(OWMApi, self).__init__('owm')
        self.lang = 'en'
        self.observation = ObservationParser()
        self.forecast = ForecastParser()

    def build_query(self, params):
        params.get('query').update({'lang': self.lang})
        return params.get('query')

    def get_data(self, response):
        return response.text

    def weather_at_place(self, name):
        data = self.request({
            'path': '/weather',
            'query': {'q': name}
        })
        return self.observation.parse_JSON(data)

    def three_hours_forecast(self, name):
        data = self.request({
            'path': '/forecast',
            'query': {'q': name}
        })
        return self.to_forecast(data, '3h')

    def daily_forecast(self, name, limit=None):
        query = {'q': name}
        if limit is not None:
            query['cnt'] = limit
        data = self.request({
            'path': '/forecast/daily',
            'query': query
        })
        return self.to_forecast(data, 'daily')

    def to_forecast(self, data, interval):
        forecast = self.forecast.parse_JSON(data)
        if forecast is not None:
            forecast.set_interval(interval)
            return Forecaster(forecast)
        else:
            return None


class WeatherSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.__create_owm()
        self.CODES = multi_key_dict()
        self.CODES['01d', '01n'] = 0
        self.CODES['02d', '02n', '03d', '03n'] = 1
        self.CODES['04d', '04n'] = 2
        self.CODES['09d', '09n'] = 3
        self.CODES['10d', '10n'] = 4
        self.CODES['11d', '11n'] = 5
        self.CODES['13d', '13n'] = 6
        self.CODES['50d', '50n'] = 7

        self.register_intent('weather.current', self.handle_current_intent)
        self.register_intent('weather.next.hour', self.handle_next_hour_intent)
        self.register_intent('weather.next.day', self.handle_next_day_intent)

    def __create_owm(self):
        key = self.config.get('api_key')
        if key and not self.config.get('proxy'):
            self.owm = OWM(key)
        else:
            self.owm = OWMApi()

    def handle_weather(self, get_weather, intent_match, temp='temp', temp_min='temp_min',
                       temp_max='temp_max'):
        location, pretty_location = self.get_location(intent_match)
        self.__build_results(pretty_location == self.location_pretty, pretty_location, get_weather(location), temp, temp_min, temp_max)

    def handle_current_intent(self, intent_match):
        self.handle_weather(lambda l: self.owm.weather_at_place(l).get_weather(), intent_match)

    def handle_next_hour_intent(self, intent_match):
        self.handle_weather(lambda l: self.owm.three_hours_forecast(l).get_forecast().get_weathers()[0], intent_match)

    def handle_next_day_intent(self, intent_match):
        self.handle_weather(lambda l: self.owm.daily_forecast(l).get_forecast().get_weathers()[1], intent_match,
                            'day', 'min', 'max')

    def get_location(self, intent_match):
        try:
            location = intent_match.matches.get('location')
            if location is not None:
                return location, location

            location = self.location
            if type(location) is dict:
                city = location['city']
                state = city['state']
                return city['name'] + ', ' + state['name'] + ', ' + \
                    state['country']['name'], self.location_pretty

            return None
        except HTTPError:
            self.set_action('location.not.found')
            logger.warning('No location found')

    def __build_results(
            self, is_local, location_pretty, weather, temp='temp', temp_min='temp_min',
            temp_max='temp_max'):

        if not is_local:
            self.add_result('diff_location', location_pretty)
        self.add_result('location', location_pretty)
        self.add_result('scale', self.__get_temperature_unit())
        self.add_result('condition', weather.get_detailed_status())
        self.add_result('temp_current', self.__get_temperature(weather, temp))
        self.add_result('temp_min', self.__get_temperature(weather, temp_min))
        self.add_result('temp_max', self.__get_temperature(weather, temp_max))

        weather_code = str(weather.get_weather_icon_name())
        self.add_result('img_code', self.CODES[weather_code])

    def __get_temperature_unit(self):
        system_unit = self.global_config.get('system_unit')
        return system_unit == 'metric' and 'celsius' or 'fahrenheit'

    def __get_temperature(self, weather, key):
        unit = self.__get_temperature_unit()
        return str(int(math.floor(weather.get_temperature(unit)[key])))

