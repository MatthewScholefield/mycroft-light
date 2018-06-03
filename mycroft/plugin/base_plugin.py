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
import json
from abc import ABCMeta
from lazy import lazy
from os.path import join
from typing import TYPE_CHECKING

from mycroft.util import log
from mycroft.util.misc import recursive_merge

if TYPE_CHECKING:
    from mycroft.root import Root
    from mycroft.services.filesystem_service import FilesystemService


class BasePlugin(metaclass=ABCMeta):
    """
    Any dynamically loaded class

    Attributes:
        _plugin_path (str):
    """
    __version__ = '0.0.0'  # Used for deciding to run .setup()

    #: Name of full dot-separated position in tree
    #: ie. MimicTts -> 'interfaces.tts.mimic'
    _plugin_path = ''

    #: Name of attribute in root tree.
    #: ie. MimicTts -> 'mimic'
    _attr_name = ''

    #: Extra data structures to register as a value that can be set in skill packages
    #: ie. {'led_pin': int} to allow skills to assign `p.led_pin = 12`
    _package_struct = {}

    #: Default configuration to be added to the plugin's local config (self.config)
    #: ie. {'value': 'hello'} == self.config['value']
    #:     == self.rt.config['<path>']['<to>']['<plugin>']['value']
    _config = {}

    #: Default configuration to be added to the root config (self.rt.config)
    #: ie. {'val': 'hi'} == self.rt.config['val']
    _root_config = {}

    def __init__(self, rt):
        # type: (Root) -> None
        self.rt = rt

        if self._package_struct:
            self.rt.package.add_struct(self._package_struct)

        if not self._plugin_path and self._config:
            raise RuntimeError('Cannot set _config for non-dynamically loaded class {}'.format(
                self.__class__.__name__
            ))

        if 'config' in rt and self._plugin_path:
            if self._root_config:
                rt.config.inject(self._root_config)
            if self._config:
                log.debug('INJECTING CONFIG,', self._config, 'AT', self._plugin_path)
                rt.config.inject(self._config, self._plugin_path)
                log.debug('NEW CONFIG:', json.dumps(rt.config, indent=4))

            self.config = {}
            rt.config.on_change(self._plugin_path, self.on_config_change)

            self.on_config_change(rt.config.get_path(self._plugin_path))

        else:
            self.config = {}

        if 'plugin_versions' in rt:
            old_version = rt.plugin_versions.get(self._plugin_path)
            if old_version != self.__version__:
                self.setup(rt)
                rt.plugin_versions[self._plugin_path] = self.__version__

    @lazy
    def filesystem(self):
        # type: () -> FilesystemService
        subdir = join('config', *self._plugin_path.split('.'))
        return self.rt.filesystem.subdir(subdir)

    @staticmethod
    def setup(rt):
        # type: (Root) -> None
        """Override to provide an installation script. Run once before loading or after updating"""
        pass

    def on_config_change(self, config: dict):
        self.config = dict(recursive_merge(self.config, config))
