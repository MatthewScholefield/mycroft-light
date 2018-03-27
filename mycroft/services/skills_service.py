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
import os
import sys
from importlib import import_module, reload
from inspect import isclass
from os import listdir
from os.path import isdir, join, dirname, basename
from subprocess import call

import pyinotify

from mycroft.group_plugin import GroupPlugin
from mycroft.services.service_plugin import ServicePlugin
from mycroft.skill_plugin import SkillPlugin
from mycroft.util import log
from mycroft.util.git_repo import GitRepo
from mycroft.util.misc import safe_run
from mycroft.util.text import to_camel


class EventHandler(pyinotify.ProcessEvent):
    exts = ['.py', '.intent', '.entity']

    def __init__(self, skills):
        super().__init__()
        self.skills = skills

    def process_default(self, event):
        for folder in event.path.split('/'):
            if folder.endswith('_skill'):
                if any(event.name.endswith(ext) for ext in self.exts):
                    self.skills.reload(folder)


class SkillsService(ServicePlugin, GroupPlugin):
    """Dynamically loads skills"""

    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)

        self.git_repo = GitRepo(directory=self.rt.paths.skills,
                                url='https://github.com/MatthewScholefield/mycroft-light.git',
                                branch='skills',
                                update_freq=1)
        self.blacklist = self.config['blacklist']
        sys.path.append(self.rt.paths.skills)

        log.info('Loading skills...')
        GroupPlugin.__init__(self, SkillPlugin, 'mycroft.skills', '_skill')
        self.error_label = 'Loading skill'
        for cls in self._classes.values():
            cls.rt = rt
        self._init_plugins()
        log.info('Finished loading skills.')

        # The watch manager stores the watches and provides operations on watches
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO
        skills_dir = self.rt.paths.skills

        handler = EventHandler(self)
        notifier = pyinotify.ThreadedNotifier(wm, handler)
        notifier.daemon = True
        wm.add_watch(skills_dir, mask, rec=True)
        notifier.start()

    def reload(self, folder_name):
        log.debug('Reloading', folder_name + '...')
        skill_name = folder_name.replace(self._suffix, '')

        if skill_name in self._plugins:
            self._plugins[skill_name]._unload()
            del self._plugins[skill_name]

        if skill_name in self._classes:
            self.rt.intent.remove_skill(skill_name)
            del self._classes[skill_name]

        cls = self.load_skill_class(folder_name)
        if not cls:
            return

        cls._attr_name = self._make_name(cls)
        cls.rt = self.rt
        self._classes[skill_name] = cls

        def init():
            self._plugins[skill_name] = cls()
            return True

        if safe_run(init, label='Reloading ' + skill_name):
            self.rt.intent.all.compile()
            log.info('Reloaded', folder_name)

    def load_skill_class(self, folder_name):
        cls_name = to_camel(folder_name)

        try:
            mod = import_module(folder_name + '.skill')
            mod = reload(mod)
            cls = getattr(mod, cls_name, '')
        except Exception:
            log.exception('Loading', folder_name)
            return None

        if not isclass(cls):
            log.error('Could not find', cls_name, 'in', folder_name)
            return None

        return cls

    def _load_classes(self, package, suffix):
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
        log.info('Loading classes...')
        # Temporary while skills are monolithic
        skills_dir = self.rt.paths.skills
        if isdir(skills_dir) and not isdir(join(skills_dir, '.git')):
            call(['mv', skills_dir, join(dirname(skills_dir), 'skills-old')])

        self.git_repo.try_pull()
        # End temporary

        classes = {}
        folder_names, invalid_names = listdir(self.rt.paths.skills), []

        for folder_name in folder_names:
            if not folder_name.endswith(suffix):
                invalid_names.append(folder_name)
                continue

            cls = self.load_skill_class(folder_name)
            if not cls:
                continue

            cls._attr_name = self._make_name(cls)
            if cls._attr_name not in self.blacklist:
                classes[cls._attr_name] = cls

        log.info('Skipped folders:', ', '.join(invalid_names))
        return classes
