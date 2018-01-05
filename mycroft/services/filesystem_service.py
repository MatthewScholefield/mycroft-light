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
from os import makedirs
from os.path import join, isfile, isdir, expanduser

from mycroft.services.service_plugin import ServicePlugin


class FilesystemService(ServicePlugin):
    def __init__(self, rt, root=None):
        super().__init__(rt)
        self.root = root or expanduser(rt.paths.user_config)
        if not isdir(''):
            self.mkdir('')

    def path(self, file):
        return join(self.root, file)

    def subdir(self, subdir):
        return FilesystemService(self.rt, self.path(subdir))

    def open(self, file, mode='r'):
        return open(self.path(file), mode)

    def isfile(self, file):
        return isfile(self.path(file))

    def isdir(self, dr):
        return isdir(self.path(dr))

    def mkdir(self, dr):
        makedirs(self.path(dr), exist_ok=True)
