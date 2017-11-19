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

from datetime import datetime
from difflib import SequenceMatcher
from time import time as get_time
from time import mktime

import json
from parsedatetime import Calendar
from threading import Timer

from mycroft import MycroftSkill
from twiggy import log


class TodoSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.register_intent('show', self.show)
        self.register_intent('add', self.add)
        self.register_intent('remove', self.remove)
        self.register_intent('remove.all', self.remove_all)
        self.data_name = 'todo.json'

        if not self.is_file(self.data_name):
            self.todo = []
            self.save()
        else:
            self.todo = self.load_todo()

    def load_todo(self):
        return json.load(self.open_file(self.data_name))

    def save(self):
        with self.open_file(self.data_name, 'w') as f:
            f.write(json.dumps(self.todo, indent=4, sort_keys=True))

    def show(self):
        if len(self.todo) == 0:
            self.set_action('no.items')
            return 0.7
        self.add_result('tasks', ', '.join(entry['task'] for entry in self.todo))
        return 0.8

    def add(self, data):

        if 'task' not in data.matches:
            self.set_action('no.task')
            return 0.6

        task = data.matches['task']
        entry = {
            'time': get_time(),
            'task': task
        }

        def callback():
            self.todo.append(entry)
            self.save()

        self.set_callback(callback)
        self.add_result('task', task)

        return 0.8
    
    def remove_all(self, data):
        def callback():
            self.todo = []
            self.save()
        self.set_callback(callback)
        return 0.8 if len(self.todo) > 0 else 0.7

    def remove(self, data):
        task = data.matches['task']

        if task in ['all', 'everything']:
            self.set_action('remove.all')
            return self.remove_all()

        similarities = [SequenceMatcher(a=task, b=i['task']).ratio() for i in self.todo]
        similarity = 0.0 if len(self.todo) == 0 else max(similarities)
        if similarity < 0.5:
            self.add_result('task', task)
            self.set_action('remove.not.found')
            return 0.6

        index = similarities.index(similarity)

        def callback():
            self.add_result('task', self.todo[index]['task'])
            del self.todo[index]
            self.save()
        self.set_callback(callback)
        return 0.8
