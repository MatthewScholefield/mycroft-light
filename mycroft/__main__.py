#!/usr/bin/env python3
#
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
#
import os
import sys

sys.path.append(os.path.abspath('.'))

from requests.exceptions import HTTPError, ConnectionError

from mycroft.clients.enclosure_client import EnclosureClient
from mycroft.clients.websocket_client import WebsocketClient

from mycroft.api import load_device_info
from mycroft.configuration import ConfigurationManager
from mycroft.clients.speech_client import SpeechClient
from mycroft.clients.text_client import TextClient
from mycroft.managers.client_manager import ClientManager
from mycroft.managers.format_manager import FormatManager
from mycroft.managers.intent_manager import IntentManager
from mycroft.managers.path_manager import PathManager
from mycroft.managers.query_manager import QueryManager
from mycroft.managers.skill_manager import SkillManager

from twiggy import log
from mycroft import main_thread
from mycroft.util.log import setup_logging


def info(message):
    print(message)
    log.info(message)


def main():
    ConfigurationManager.init()
    config = ConfigurationManager.get()
    setup_logging(config)

    if config['use_server']:
        try:
            info('Loading device info...')
            load_device_info()

            info('Loading remote settings...')
            ConfigurationManager.load_remote()
        except (HTTPError, ConnectionError):
            info('Failed to authenticate.')

    if len(sys.argv) > 1:
        letters = ''.join(sys.argv[1:]).lower()
    else:
        letters = 'wtse'
    clients = []
    for c, cls in [
        ('w', WebsocketClient),
        ('t', TextClient),
        ('s', SpeechClient),
        ('e', EnclosureClient)
    ]:
        if c in letters:
            clients.append(cls)
    info('Starting clients: ' + ', '.join(cls.__name__ for cls in clients))

    path_manager = PathManager()
    intent_manager = IntentManager(path_manager)
    formats = FormatManager(path_manager)
    query_manager = QueryManager(intent_manager, formats)
    skill_manager = SkillManager(path_manager, intent_manager, query_manager)

    if not config['use_server']:
        skill_manager.blacklist += ['PairingSkill', 'ConfigurationSkill']

    log.debug('Starting clients...')
    client_manager = ClientManager(clients, path_manager, query_manager, formats)
    log.debug('Started clients.')

    info('Loading skills...')
    skill_manager.load_skills()
    info('Loaded skills.')
    intent_manager.on_intents_loaded()
    log.debug('Executed on intents loaded callback.')

    client_manager.start()
    try:
        main_thread.wait_for_quit()
    except KeyboardInterrupt:
        pass
    finally:
        log.debug('Quiting!')
        client_manager.on_exit()


if __name__ == '__main__':
    main()
