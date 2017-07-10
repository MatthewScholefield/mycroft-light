from requests import HTTPError

from mycroft.api import DeviceApi
from mycroft.configuration import ConfigurationManager
from mycroft.skill import ScheduledSkill


class ConfigurationSkill(ScheduledSkill):
    def __init__(self):
        super().__init__()
        self.set_delay(self.config.get('max_delay'))
        self.api = DeviceApi()
        self.config_hash = ''
        self.register_intent('update.config', self.update)

    def on_triggered(self):
        self.update()

    def update(self):
        config = self.api.get_settings()
        location = self.api.get_location()
        if location:
            config["location"] = location

        if self.config_hash != hash(str(config)):
            def callback():
                ConfigurationManager.load_defaults()
                self.config_hash = hash(str(config))
            self.set_callback(callback)
            self.set_action('config.updated')
        else:
            self.set_action('config.no_change')
