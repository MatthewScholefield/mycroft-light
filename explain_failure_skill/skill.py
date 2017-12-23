# Copyright (c) 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Simple
# (see https://github.com/MatthewScholefield/mycroft-simple).
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

from subprocess import check_output

from padatious.match_data import MatchData

from mycroft import MycroftSkill


class ExplainFailureSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.log_file = self.rt.config['log_file']
        self.register_intent('why.did.skill.fail', self.why_did_skill_fail)
        self.register_entity('skill')

    def why_did_skill_fail(self, data: MatchData):
        skill = data.matches['skill']
        skill = skill.title().replace(' ', '')
        self.add_result('skill', skill)
        error = check_output('cat ' + self.log_file + ' | grep -A30 "' + skill + '" | grep -E ^[A-Z][a-z]*Error | head -n1',shell=True)
        if error:
            self.add_result('error', error.decode())
            return 0.8
        else:
            self.set_action('skill.not.found')
            return 0.6
