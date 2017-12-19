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

import re
import sys
from importlib import import_module, reload
from os import listdir
from os.path import isdir, join, dirname, basename
from subprocess import call

from threading import Thread

from mycroft import MycroftSkill
from mycroft.configuration import ConfigurationManager
from twiggy import log
from mycroft.util.text import to_camel
from mycroft.util.git_repo import GitRepo
import pyinotify


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, skill_loader):
        super().__init__()
        self.skill_loader = skill_loader

    def process_default(self, event):
        skill_name = basename(event.path)
        if event.name == 'skill.py' and skill_name.endswith('_skill'):
            self.skill_loader.load_skill(skill_name)
            log.info("Reloaded: {}", skill_name)


class SkillLoader:
    """Dynamically loads skills"""

    def __init__(self, path_manager, intent_manager, query_manager):
        MycroftSkill.initialize_references(path_manager, intent_manager, query_manager)
        self.path_manager = path_manager
        self.intent_manager = intent_manager
        self.skills = {}
        self.git_repo = GitRepo(directory=self.path_manager.skills_dir,
                                url='https://github.com/MatthewScholefield/mycroft-light.git',
                                branch='skills',
                                update_freq=1)
        self.blacklist = ConfigurationManager.get()['skills']['blacklist']


        # The watch manager stores the watches and provides operations on watches
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO
        skills_dir = self.path_manager.skills_dir

        handler = EventHandler(self)
        notifier = pyinotify.ThreadedNotifier(wm, handler)
        notifier.daemon = True
        wdd = wm.add_watch(skills_dir, mask, rec=True)
        notifier.start()

    def load_skill(self, skill_name, on_message=lambda _: None):
        cls_name = to_camel(skill_name)
        if cls_name in self.blacklist:
            on_message('Skipping ' + cls_name + '.')
            return

        if skill_name in self.skills:
            self.intent_manager.remove_skill(cls_name)

        try:
            mod = import_module(skill_name + '.skill')
            mod = reload(mod)
            cls = getattr(mod, cls_name)
            self.skills[skill_name] = cls()
            on_message('Loaded ' + cls_name + '.')
        except:
            log.trace('error').error('loading ' + cls_name)
            on_message('Failed to load ' + cls_name + '!')

    def load_skills(self, on_message):
        """
        Looks in the skill folder and loads the
        CamelCase equivalent class of the snake case folder
        This class should be inside the skill.py file. Example:

        skills/
            time_skill/
                skill.py - class TimeSkill(MycroftSkill):
            weather_skill/
                skill.py - class WeatherSkill(MycroftSkill):
        """

        # Temporary while skills are monolithic
        skills_dir = self.path_manager.skills_dir
        if isdir(skills_dir) and not isdir(join(skills_dir, '.git')):
            call(['mv', skills_dir, join(dirname(skills_dir), 'skills-old')])

        self.git_repo.try_pull()
        # End temporary

        threads = []
        sys.path.append(self.path_manager.skills_dir)
        skill_names, invalid_names = listdir(self.path_manager.skills_dir), []
        for skill_name in skill_names:
            if not re.match('^[a-z][a-z_]*_skill$', skill_name):
                invalid_names.append(skill_name)
                continue

            t = Thread(target=lambda: self.load_skill(skill_name, on_message))
            t.start()
            threads.append(t)
        for i in threads:
            i.join()

        log.debug('Skipped folders: {}', ', '.join(invalid_names))
