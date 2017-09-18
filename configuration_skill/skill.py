from mycroft.api import DeviceApi, is_paired
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

    def reload(self):
        ConfigurationManager.load_remote()
        self.config_hash = hash(str(ConfigurationManager.get()))

    def update(self):
        if not is_paired():
            return
        if self.config_hash != hash(str(self.api.get_settings())):
            self.set_callback(self.reload)
            self.set_action('config.updated')
        else:
            self.set_action('config.no_change')
