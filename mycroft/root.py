from mycroft.group_plugin import GroupPlugin
from mycroft.services.config_service import ConfigService
from mycroft.services.device_info_service import DeviceInfoService
from mycroft.services.filesystem_service import FilesystemService
from mycroft.services.formats_service import FormatsService
from mycroft.services.frontends_service import FrontendsService
from mycroft.services.identity_service import IdentityService
from mycroft.services.intent_service import IntentService
from mycroft.services.main_thread_service import MainThreadService
from mycroft.services.paths_service import PathsService
from mycroft.services.query_service import QueryService
from mycroft.services.service_plugin import ServicePlugin
from mycroft.services.skills_service import SkillsService


class Root(GroupPlugin):
    """Class to help autocomplete determine types of dynamic root object"""

    def __init__(self):
        super().__init__(ServicePlugin, 'mycroft.services', '_service')
        self._init_plugins(self, gp_order=[
            'config', 'paths', 'filesystem', 'identity',
            'device_info', 'query', 'formats', 'frontends',
            'intent', 'skills', 'main_thread'
        ])

    def __type_hinting__(self):
        self.config = ''  # type: ConfigService
        self.paths = ''  # type: PathsService
        self.filesystem = ''  # type: FilesystemService
        self.identity = ''  # type: IdentityService
        self.device_info = ''  # type: DeviceInfoService
        self.query = ''  # type: QueryService
        self.formats = ''  # type: FormatsService
        self.frontends = ''  # type: FrontendsService
        self.intent = ''  # type: IntentService
        self.skills = ''  # type: SkillsService
        self.main_thread = ''  # type: MainThreadService
