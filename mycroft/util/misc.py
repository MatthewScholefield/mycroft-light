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
from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

from mycroft.util.log import LOG


def safe_run(callback, warn=True, *args):
    """Runs code, logging exceptions rather than throwing them"""
    try:
        callback()
    except:
        LOG.print_trace(*args, warn=warn)


@contextmanager
def redirect_alsa_errors():
    """
    Redirects ALSA errors to logger rather than stdout
    Warning: This seems to crash on Raspbian Jessie

    Usage:
        with redirect_alsa_errors():
            do_something_that_generates_alsa_errors()
    """
    func_type = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

    def alsa_err_handler(filename, line, function, err, fmt):
        del line
        del err
        LOG('alsa').debug(
            filename.decode() + ':' + function.decode() + ', ' + fmt.decode())

    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(func_type(alsa_err_handler))
    yield
    asound.snd_lib_error_set_handler(None)
