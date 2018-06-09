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
import inspect
from abc import abstractmethod, ABCMeta
from time import strftime, gmtime
from traceback import format_exc

import atexit


class Level:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    EXCEPTION = 4


class BaseLogger(metaclass=ABCMeta):
    fn_names = [
        'debug',
        'info',
        'warning',
        'error',
        'exception'
    ]

    ignore_functions = [
        'safe_run'
    ]

    @abstractmethod
    def write(self, text):
        pass

    def _shorten_mod(self, mod_name):
        def is_ess(i, s):
            return len(s[:i + 1].split('.')[-1]) <= 2

        i = 0
        while len(mod_name) > 20 and i < len(mod_name):
            if is_ess(i, mod_name):
                i += 1
                continue
            mod_name = mod_name[:i] + mod_name[i + 1:]

        mod_name = ' ' * (20 - len(mod_name)) + mod_name

        return mod_name

    def _get_function_info(self, offset):
        offset += 1
        # Stack:
        # [0] - _get_function_info()
        # [1] - _get_prefix()
        # [1] - debug(), info(), warning(), or error()
        # [2] - caller
        stack = inspect.stack()

        # Record:
        # [0] - frame object
        # [1] - filename
        # [2] - line number
        # [3] - function
        # ...
        try:
            if len(stack) <= offset:
                if offset == 0:
                    return ''
                return self._get_function_info(offset - 1)
            record = stack[offset]
            mod = inspect.getmodule(record[0])
            module_name = mod.__name__ if mod else ''
            function_name = record[3]
            line_no = record[2]
            if function_name in self.ignore_functions:
                if len(stack) > offset + 1:
                    return self._get_function_info(offset + 1)
                return ''
            return self._shorten_mod(module_name) + ':' + '{:03}'.format(line_no)
        except Exception:
            return ''

    def _get_prefix(self, level, offset):
        prefix = ' | '.join([
            strftime('%m/%d %H:%M:%S', gmtime()),
            self._get_function_info(offset + 1),
            ' ' * (5 - len(self.fn_names[level])) + self.fn_names[level].upper(),
            ''
        ])
        return prefix

    def __init__(self, level):
        for i in range(level):
            setattr(self, self.fn_names[i], lambda *args, **kwargs: None)

    def __format(self, args, kwargs):
        end = '' if not kwargs else (': ' + str(kwargs))
        return ' '.join(map(str, args)) + end

    def __log(self, level, args, kwargs):
        offset = kwargs.pop('stack_offset', 0)
        self.write(self._get_prefix(level, offset + 2) + self.__format(args, kwargs) + '\n')

    def debug(self, *args, **kwargs):
        self.__log(Level.DEBUG, args, kwargs)

    def info(self, *args, **kwargs):
        self.__log(Level.INFO, args, kwargs)

    def warning(self, *args, **kwargs):
        self.__log(Level.WARNING, args, kwargs)

    def error(self, *args, **kwargs):
        self.__log(Level.ERROR, args, kwargs)

    def exception(self, *args, **kwargs):
        info = self._get_prefix(Level.EXCEPTION, kwargs.pop('stack_offset', 0) + 1)
        self.write(info + '\n\n=== ' + self.__format(args, kwargs) + ' ===' + '\n' + format_exc() + '\n')


class FileLogger(BaseLogger):
    def __init__(self, filename, level):
        super().__init__(level)
        self.file = open(filename, 'w')
        atexit.register(self.file.close)

    def write(self, text):
        self.file.write(text)
        self.file.flush()


class PrintLogger(BaseLogger):
    def write(self, text):
        print(text, end='', flush=True)


log = FileLogger('/var/tmp/mycroft.log', Level.DEBUG)
