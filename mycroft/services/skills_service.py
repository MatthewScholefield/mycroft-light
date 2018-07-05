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
import sys

import pyinotify
from importlib import import_module, reload
from inspect import isclass
from os import listdir
from os.path import isdir, join, dirname, isfile
from subprocess import call

from mycroft.plugin.group_plugin import GroupPlugin, GroupMeta
from mycroft.plugin.util import update_dyn_attrs
from mycroft.services.service_plugin import ServicePlugin
from mycroft.skill_plugin import SkillPlugin
from mycroft.util import log
from mycroft.util.git_repo import GitRepo
from mycroft.util.misc import safe_run
from mycroft.util.text import to_camel


class EventHandler(pyinotify.ProcessEvent):
    exts = ['.py', '.intent', '.entity', '.txt', '.voc']

    def __init__(self, skills, folder):
        super().__init__()
        self.skills = skills
        self.folder = folder

    def process_default(self, event):
        parts = event.path.replace(self.folder, '').split('/')
        if len(parts) < 2:
            return

        skill_folder = parts[1]
        if skill_folder.endswith('_skill'):
            if any(event.name.endswith(ext) for ext in self.exts):
                self.skills.reload(skill_folder)


class SkillsService(ServicePlugin, GroupPlugin, metaclass=GroupMeta, base=SkillPlugin,
                    package='', suffix='_skill'):
    """Dynamically loads skills"""
    _config = {
        'blacklist': [],
        'url': 'https://github.com/MatthewScholefield/mycroft-light.git',
        'branch': 'skills',
        'update_freq': 1
    }

    def __init__(self, rt):
        ServicePlugin.__init__(self, rt)
        sys.path.append(self.rt.paths.skills)

        def inject_rt(cls):
            cls.rt = rt

        log.info('Loading skills...')
        GroupPlugin.__init__(self, gp_alter_class=inject_rt, gp_blacklist=self.config['blacklist'],
                             gp_timeout=10.0, gp_daemon=True)
        for name, thread in self._init_threads.items():
            if thread.is_alive():
                log.warning('Skill init method taking too long for:', name)
        log.info('Finished loading skills.')

        # The watch manager stores the watches and provides operations on watches
        wm = pyinotify.WatchManager()
        mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO
        skills_dir = self.rt.paths.skills

        handler = EventHandler(self, skills_dir)
        notifier = pyinotify.ThreadedNotifier(wm, handler)
        notifier.daemon = True
        wm.add_watch(skills_dir, mask, rec=True, auto_add=True)
        notifier.start()
        self.git_repo = self.create_git_repo()

    def create_git_repo(self):
        config = self.rt.config.get_path(self._plugin_path)
        return GitRepo(directory=self.rt.paths.skills,
                       url=config['url'],
                       branch=config['branch'],
                       update_freq=config['update_freq'])

    def reload(self, folder_name):
        log.debug('Reloading', folder_name + '...')
        skill_name = folder_name.replace(self._suffix_, '')

        if skill_name in self._plugins:
            safe_run(self._plugins[skill_name]._unload, label='Skill unload')
            del self._plugins[skill_name]

        if skill_name in self._classes:
            self.rt.intent.remove_skill(skill_name)
            del self._classes[skill_name]

        if not isfile(join(self.rt.paths.skills, folder_name, 'skill.py')):
            return

        cls = self.load_skill_class(folder_name)
        if not cls:
            return

        cls.rt = self.rt
        self._classes[skill_name] = cls

        def init():
            self._plugins[skill_name] = cls()
            return True

        if safe_run(
                init, label='Reloading ' + skill_name, custom_exception=NotImplementedError,
                custom_handler=lambda e, l: log.info(l + ': Skipping disabled plugin')
        ):
            self.rt.intent.context.compile()
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

        update_dyn_attrs(cls, '_skill', self._plugin_path)
        return cls

    def setup(self):
        skills_dir = self.rt.paths.skills
        if isdir(skills_dir) and not isdir(join(skills_dir, '.git')):
            call(['mv', skills_dir, join(dirname(skills_dir), 'skills-old')])
        self.create_git_repo().try_pull()

    def _on_partial_load(self, plugin_name):
        self.rt.intent.remove_skill(plugin_name)

    def _load_classes(self, package, suffix, blacklist):
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
        self.setup()

        classes = {}
        folder_names, invalid_names = listdir(self.rt.paths.skills), []

        for folder_name in folder_names:
            if not folder_name.endswith(suffix) or \
                    not isfile(join(self.rt.paths.skills, folder_name, 'skill.py')):
                invalid_names.append(folder_name)
                continue

            attr_name = folder_name[:-len(suffix)]
            if attr_name in blacklist:
                continue

            cls = self.load_skill_class(folder_name)
            if not cls:
                continue

            classes[attr_name] = cls

        log.info('Skipped folders:', ', '.join(invalid_names))
        return classes
