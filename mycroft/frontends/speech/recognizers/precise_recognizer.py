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
from os import mkdir
from os.path import expanduser, isdir, join, isfile
from subprocess import call, PIPE, Popen
from threading import Thread
from time import time as get_time

from mycroft.frontends.speech.recognizers.recognizer_plugin import RecognizerPlugin
from mycroft.util import log


class PreciseRecognizer(RecognizerPlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.update_freq = 24  # in hours
        self.url_base = 'https://raw.githubusercontent.com/MycroftAI/precise-data/'
        self.exe_name = 'precise-stream'

        ww = self.listener_config['wake_word']
        model_name = ww.replace(' ', '-') + '.pb'
        model_folder = expanduser('~/.mycroft/precise')
        if not isdir(model_folder):
            mkdir(model_folder)
        model_path = join(model_folder, model_name)

        exe_file = self.find_download_exe()
        log.info('Found precise executable: ' + exe_file)
        self.update_model(model_name, model_path)

        args = [exe_file, model_path, '1024']
        self.proc = Popen(args, stdin=PIPE, stdout=PIPE)
        self.has_found = False
        self.cooldown = 20
        t = Thread(target=self.check_stdout)
        t.daemon = True
        t.start()

    def find_download_exe(self):
        exe_file = join(self.rt.paths.user_config, self.exe_name)
        if exe_file:
            return exe_file
        try:
            if call(self.exe_name + ' < /dev/null', shell=True) == 0:
                return self.exe_name
        except OSError:
            pass

        import platform
        import stat

        def snd_msg(cmd):
            """Send message to faceplate"""
            Popen('echo "' + cmd + '" > /dev/ttyAMA0', shell=True)

        arch = platform.machine()
        exe_file = expanduser('~/.mycroft/precise/' + self.exe_name)
        url = self.url_base + 'dist/' + arch + '/' + self.exe_name

        snd_msg('mouth.text=Updating Listener...')
        self.download(url, exe_file)
        snd_msg('mouth.reset')

        os.chmod(exe_file, os.stat(exe_file).st_mode | stat.S_IEXEC)
        Popen('echo "mouth.reset" > /dev/ttyAMA0', shell=True)
        return exe_file

    @staticmethod
    def download(url, filename):
        import shutil
        from urllib.request import urlopen
        log.info('Downloading: ' + url)
        req = urlopen(url)
        with open(filename, 'wb') as fp:
            shutil.copyfileobj(req, fp)

    def update_model(self, name, file_name):
        if isfile(file_name):
            stat = os.stat(file_name)
            if get_time() - stat.st_mtime < self.update_freq * 60 * 60:
                return
        name = name.replace(' ', '%20')
        url = self.url_base + 'models/' + name
        self.download(url, file_name)
        self.download(url + '.params', file_name + '.params')

    def check_stdout(self):
        while True:
            line = self.proc.stdout.readline()
            if self.cooldown > 0:
                self.cooldown -= 1
                self.has_found = False
                continue
            if float(line) > 0.5:
                self.has_found = True
            else:
                self.has_found = False

    def update(self, chunk):
        self.proc.stdin.write(chunk)
        self.proc.stdin.flush()

    def found_wake_word(self, frame_data):
        if self.has_found and self.cooldown == 0:
            self.cooldown = 20
            return True
        return False
