#!/usr/bin/env python3
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
import sys

sys.path += ['.']  # noqa

from argparse import ArgumentParser
from time import sleep


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('setup')
    args = parser.parse_args()
    if args.action == 'setup':
        import mycroft.util
        from mycroft.util.log import PrintLogger, Level
        mycroft.util.log = PrintLogger(Level.INFO)
        mycroft.util.log._get_prefix = lambda level, offset: ''

    from mycroft.util import log
    from mycroft.root import Root

    if args.action == 'setup':
        Root(None, blacklist=['skills'])
        return

    rt = Root()

    if rt.config['use_server'] and rt.device_info:
        rt.config.load_remote()

    rt.intent.context.compile()
    rt.interfaces.all.run(gp_daemon=True)

    try:
        rt.main_thread.wait()
    except KeyboardInterrupt:
        pass
    log.info('Quiting...')
    sleep(0.1)
    print()


if __name__ == '__main__':
    main()
