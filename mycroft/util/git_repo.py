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
from os import getcwd, chdir

from git import Git
from os.path import isdir, join
from subprocess import call
from time import time


class GitRepo:
    def __init__(self, directory, url, branch, update_freq=1, tag=None):
        self.dir = directory
        self.url = url
        self.branch = branch
        self.update_freq = update_freq  # Hours
        self.tag = tag
        self.git = Git(self.dir)

    def run_inside(self, command):
        cur_path = getcwd()
        if command.startswith('./'):
            command = join(self.dir, command[2:])
        try:
            chdir(self.dir)
            if isinstance(command, str):
                call(command.split(' '))
            else:
                call(command)
        finally:
            chdir(cur_path)

    def _clone(self):
        if self.tag is None:
            self.git.clone(self.url, self.dir, branch=self.branch, single_branch=True, depth=1)
        else:
            self.git.init()
            self.git.remote('add', 'origin', self.url)
            self.git.fetch('origin', self.tag, depth=1)
            self.git.reset('FETCH_HEAD', hard=True)

    def try_pull(self):
        if not isdir(self.dir):
            self._clone()
            return True

        git_folder = join(self.dir, '.git')
        stat = os.stat(git_folder)
        if time() - stat.st_mtime > self.update_freq * 60 * 60:
            # Touch folder
            os.utime(git_folder)
            if not self.tag:
                self.git.pull(ff_only=True)
            return True
        return False
