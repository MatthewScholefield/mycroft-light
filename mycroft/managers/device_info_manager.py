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
from mycroft.api import DeviceApi
from mycroft.managers.manager_plugin import ManagerPlugin


class DeviceInfoManager(ManagerPlugin, dict):
    def __init__(self, rt):
        ManagerPlugin.__init__(self, rt)
        dict.__init__(self)
        if not rt.config['use_server']:
            raise NotImplementedError('Server Disabled')
        self.reload()

    def reload(self):
        self.update(DeviceApi(self.rt).get())
