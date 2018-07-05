from os.path import join

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util.saved_json import SavedJson


class PluginVersionsService(ServicePlugin, SavedJson):
    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        SavedJson.__init__(self, join(self.filesystem.root, 'versions.json'))
