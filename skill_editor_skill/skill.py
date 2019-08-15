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
from difflib import SequenceMatcher
from mycroft_core import MycroftSkill, Package
from os.path import join
from subprocess import call

from mycroft.skill_plugin import intent_prehandler


class SkillEditorSkill(MycroftSkill):
    _required_attributes = ['desktop-interface']

    def edit_or_open_prehandler(self, p: Package):
        skill_query = p.match['skill']
        skills = list(self.rt.skills)
        skill_scores = [SequenceMatcher(a=skill_query, b=i).ratio() for i in skills]
        max_score = max(skill_scores)
        max_name = skills[skill_scores.index(max_score)]
        p.confidence = max_score ** 4
        folder = self.rt.paths.skill_dir(max_name)
        p.data = {
            'skill': max_name,
            'folder': folder,
            'file': join(folder, 'skill.py')
        }
        return p

    @intent_prehandler('edit.skill')
    def handle_edit_skill(self, p: Package):
        p.action = 'editing'
        return self.edit_or_open_prehandler(p)

    @handle_edit_skill.handler
    def handle_edit_skill(self, p: Package):
        call(['xdg-open', p.data['file']])

    @intent_prehandler('open.skill')
    def handle_open_skill(self, p: Package):
        p.action = 'opening'
        return self.edit_or_open_prehandler(p)

    @handle_open_skill.handler
    def handle_open_skill(self, p: Package):
        call(['xdg-open', p.data['folder']])
