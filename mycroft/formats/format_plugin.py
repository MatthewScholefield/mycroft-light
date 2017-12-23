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

from abc import abstractmethod
from os.path import isfile, join

from mycroft.base_plugin import BasePlugin
from mycroft.util import log


class FormatPlugin(BasePlugin):
    """
    Base class to provide an interface for different types of \"formats\"

    Formats are modes to display key-value data.
    For instance, the DialogFormat puts data into sentences
    The EnclosureFormat could put data into visual faceplate animations

    Args:
        extension (str): File extension of format to handle
        attr_name (str): Name of attribute in format manager (formats.XXXXX)
    """

    def __init__(self, rt, extension):
        super().__init__(rt)
        self._extension = extension
        self.config = rt.config.get(self.__class__.__name__, {})

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def generate_format(self, file, data):
        """
        Function to override to actually generate the format
        Args:
            file (file): Text file object of given extension
            data (dict): dict containing all data from skill
        """
        pass

    def generate(self, name, data):
        """
        Translate the data into different formats
        Depending on the format, this can be accessed different ways
        Args:
            name (IntentName): full intent name
            data (dict): dict containing all data from the skill
        Returns:
            bool: Whether the data could be generated
        """
        for dir_fn in [self.rt.paths.skill_vocab, self.rt.paths.skill_formats]:
            file_name = join(dir_fn(name.skill), name.intent + self._extension)
            if isfile(file_name):
                with open(file_name, 'r') as file:
                    log.debug('Generating', self.__class__.__name__ + '...')
                    self.generate_format(file, data)
                return True
        return False
