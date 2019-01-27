from pyowm.webapi25.forecaster import Forecaster
from pyowm.webapi25.forecastparser import ForecastParser
from pyowm.webapi25.observationparser import ObservationParser

from mycroft.api import Api


class MycroftOWM(Api):
    """
    Wrapper that defaults to the Mycroft cloud proxy so user's don't need
    to get their own OWM API keys
    """

    def __init__(self, rt):
        super().__init__(rt, "owm")
        self.lang = "en"
        self.observation = ObservationParser()
        self.forecast = ForecastParser()

    def build_query(self, params):
        params.get("query").update({"lang": self.lang})
        return params.get("query")

    def get_data(self, response):
        return response.text

    def weather_at_place(self, name, lat, lon):
        if lat and lon:
            q = {"lat": lat, "lon": lon}
        else:
            q = {"q": name}

        data = self.request({
            "path": "/weather",
            "query": q
        })
        return self.observation.parse_JSON(data)

    def three_hours_forecast(self, name, lat, lon):
        if lat and lon:
            q = {"lat": lat, "lon": lon}
        else:
            q = {"q": name}

        data = self.request({
            "path": "/forecast",
            "query": q
        })
        return self.to_forecast(data, "3h")

    def __daily_forecast(self, q: dict, limit=None):
        if limit is not None:
            q["cnt"] = limit
        data = self.request({
            "path": "/forecast/daily",
            "query": q
        })
        return self.to_forecast(data, "daily")

    def daily_forecast_at_coords(self, lat, lon, limit=None):
        return self.__daily_forecast({"lat": lat, "lon": lon})

    def daily_forecast(self, name):
        return self.__daily_forecast({"q": name})

    def to_forecast(self, data, interval):
        forecast = self.forecast.parse_JSON(data)
        if forecast is not None:
            forecast.set_interval(interval)
            return Forecaster(forecast)
        else:
            return None
