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
from fitipy import Fitipy
from os import makedirs
from os.path import join, isfile, isdir, expanduser

from mycroft.services.service_plugin import ServicePlugin


class FilesystemService(ServicePlugin, Fitipy):
    def __init__(self, rt, root=None):
        ServicePlugin.__init__(self, rt)
        Fitipy.__init__(self, root or expanduser(rt.paths.user_config))
        if not self.isdir(''):
            self.mkdir('')

    def subdir(self, *path):
        return FilesystemService(self.rt, join(self.path, *path))

    def open(self, *path, mode='r'):
        return open(join(self.path, *path), mode)

    def isfile(self, *path):
        return isfile(join(self.path, *path))

    def isdir(self, *path):
        return isdir(join(self.path, *path))

    def mkdir(self, *path):
        makedirs(self.path(join(self.path, *path)), exist_ok=True)
