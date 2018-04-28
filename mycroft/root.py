# Copyright (c) 2017 Mycroft AI, Inc.
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
from mycroft.group_plugin import GroupPlugin
from mycroft.services.config_service import ConfigService
from mycroft.services.device_info_service import DeviceInfoService
from mycroft.services.filesystem_service import FilesystemService
from mycroft.services.interfaces_service import InterfacesService
from mycroft.services.identity_service import IdentityService
from mycroft.services.intent_service import IntentService
from mycroft.services.main_thread_service import MainThreadService
from mycroft.services.package_service import PackageService
from mycroft.services.paths_service import PathsService
from mycroft.services.query_service import QueryService
from mycroft.services.scheduler_service import SchedulerService
from mycroft.services.service_plugin import ServicePlugin
from mycroft.services.skills_service import SkillsService
from mycroft.services.transformers_service import TransformersService
from mycroft.util import log


class Root(GroupPlugin):
    """Class to help autocomplete determine types of dynamic root object"""

    def __init__(self):
        super().__init__(ServicePlugin, 'mycroft.services', '_service')
        threads = self._init_plugins(self, gp_order=[
            'config', 'package', 'scheduler', 'paths', 'filesystem', 'identity',
            'device_info', 'query', 'transformers', 'interfaces',
            'intent', '*', 'skills', 'main_thread'
        ], gp_timeout=2.0, gp_daemon=True)
        for name, thread in threads.items():
            if thread.is_alive():
                log.warning('Service init method taking too long for:', name)

    def __type_hinting__(self):
        self.config = ''  # type: ConfigService
        self.paths = ''  # type: PathsService
        self.filesystem = ''  # type: FilesystemService
        self.identity = ''  # type: IdentityService
        self.device_info = ''  # type: DeviceInfoService
        self.query = ''  # type: QueryService
        self.interfaces = ''  # type: InterfacesService
        self.transformers = ''  # type: TransformersService
        self.intent = ''  # type: IntentService
        self.skills = ''  # type: SkillsService
        self.scheduler = ''  # type: SchedulerService
        self.package = ''  # type: PackageService
        self.main_thread = ''  # type: MainThreadService
