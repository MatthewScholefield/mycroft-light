# Copyright (c) 2019 Mycroft AI, Inc. and Matthew Scholefield
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
from mycroft.package_cls import Package
from mycroft.services.intent_service import UNSET_ACTION
from mycroft.services.service_plugin import ServicePlugin
from mycroft.transformers.transformer_plugin import TransformerPlugin
from mycroft.transformers.dialog_transformer import DialogTransformer
from mycroft.util import log


class TransformersService(ServicePlugin, GroupPlugin, metaclass=GroupMeta, base=TransformerPlugin,
                          package='mycroft.transformers', suffix='_transformer'):

    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        GroupPlugin.__init__(self, rt)

    def __type_hinting__(self):
        self.dialog = ''  # type: DialogTransformer

    def process(self, package: Package):
        """Called to modify attributes within package"""
        if package.action == UNSET_ACTION:
            package.action = package.match.intent_id.split(':')[1] if package.match else ''
        package.action = package.action or ''

        self.all.process(package, gp_warn=False)  # type: ignore

        log.debug('Package: \n' + str(package))
