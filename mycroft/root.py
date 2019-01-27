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
from mycroft.plugin.group_plugin import GroupPlugin, GroupMeta
from mycroft.services.config_service import ConfigService
from mycroft.services.contexts_service import ContextsService
from mycroft.services.device_info_service import DeviceInfoService
from mycroft.services.filesystem_service import FilesystemService
from mycroft.services.identity_service import IdentityService
from mycroft.services.intent_service import IntentService
from mycroft.services.interfaces_service import InterfacesService
from mycroft.services.main_thread_service import MainThreadService
from mycroft.services.package_service import PackageService
from mycroft.services.paths_service import PathsService
from mycroft.services.plugin_versions_service import PluginVersionsService
from mycroft.services.query_service import QueryService
from mycroft.services.remote_key_service import RemoteKeyService
from mycroft.services.scheduler_service import SchedulerService
from mycroft.services.service_plugin import ServicePlugin
from mycroft.services.skills_service import SkillsService
from mycroft.services.transformers_service import TransformersService
from mycroft.util import log


class Root(
    GroupPlugin, metaclass=GroupMeta,
    base=ServicePlugin, package='mycroft.services', suffix='_service'
):
    """Class to help autocomplete determine types of dynamic root object"""

    def __init__(self, timeout=2.0, blacklist=None):
        GroupPlugin.__init__(
            self, self, gp_order=[
                'config', 'package', 'scheduler', 'paths', 'filesystem', 'plugin_versions',
                'identity', 'device_info', 'remote_key', 'query', 'transformers', 'interfaces',
                'intent', '*', 'skills', 'main_thread'
            ], gp_timeout=timeout, gp_daemon=True, gp_blacklist=blacklist
        )
        for name, thread in self._init_threads.items():
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
        self.remote_key = ''  # type: RemoteKeyService
        self.plugin_versions = ''  # type: PluginVersionsService
        self.contexts = ''  # type: ContextsService
