from requests import HTTPError

from mycroft.api import DeviceApi
from mycroft.configuration import ConfigurationManager
from mycroft.skill import ScheduledSkill


class ConfigurationSkill(ScheduledSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_delay(self.config.get('max_delay'))
        self.api = DeviceApi()
        self.config_hash = ''
        self.register_intent('update.config', self.handle_update)

    def handle_update(self, intent_match):
        if self.update():
            self.set_action('config.updated')
        else:
            self.set_action('config.no_change')

    def on_triggered(self):
        self.update()

    def update(self):
        try:
            config = self.api.get_settings()
            location = self.api.get_location()
            if location:
                config["location"] = location

            if self.config_hash != hash(str(config)):
                ConfigurationManager.load_defaults()
                self.config_hash = hash(str(config))
                return True
            else:
                return False
        except HTTPError:
            return False
