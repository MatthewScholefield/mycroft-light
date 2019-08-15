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
import re
import requests
from subprocess import check_output

from mycroft_core import MycroftSkill, Package, intent_handler


class IpSkill(MycroftSkill):
    @intent_handler('ip')
    def handle_ip(self, p: Package):
        ip_info = check_output(['ip', 'addr']).decode()
        all_ips = re.finditer(r'inet (([0-9]{1,3}\.?){4})\/[0-9]{1,2}.* ([a-z0-9]+)', ip_info)
        valid_ips = []
        other_ips = []
        for match in all_ips:
            ip, label = match.group(1, 3)
            if ip in ['127.0.0.1', '0.0.0.0']:
                continue
            if label[:3] in ['wlp', 'enp']:
                valid_ips.append(ip)
            else:
                other_ips.append(ip)

        ips = valid_ips or other_ips
        spoken_ips = [(' ' + self.locale('dot.txt')[0] + ' ').join(i.split('.')) for i in ips]
        if len(ips) > 1:
            p.data.update(ips=ips)
            p.data.update(spoken_ips=spoken_ips)
        elif len(ips) == 1:
            p.data.update(ip=ips[0])
            p.data.update(spoken_ip=spoken_ips[0])

    def get_public_ip_info(self, p: Package):
        data = requests.get('https://ipinfo.io').json()
        return p.add(data={
            'ip': data['ip'],
            'hostname': data['hostname'],
            'city': data['city'],
            'region': data['region'],
            'country': data['country'],
            'loc': data['loc'],
            'postal': data['postal'],
            'org': data['org']
        })

    @intent_handler('public.ip')
    def handle_public_ip(self, p: Package):
        return self.get_public_ip_info(p)

    @intent_handler('ip.location')
    def handle_public_ip(self, p: Package):
        return self.get_public_ip_info(p)
