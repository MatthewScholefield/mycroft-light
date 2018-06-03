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
import hashlib
from os import makedirs
from urllib.error import URLError

from os.path import isdir, join, basename
from shutil import rmtree
from typing import Callable, Union, io

from requests import RequestException

from mycroft.util import log


class MycroftException(Exception):
    """Exception raised in Mycroft code that controls how it is logged"""
    def __init__(self, message, stack_trace=True):
        super().__init__(message)
        self.stack_trace = stack_trace


class _DefaultException(BaseException):
    pass


def _log_exception(label, e, warn, stack_offset):
    if warn:
        log.warning(label, '--', e.__class__.__name__ + ':', e, stack_offset=stack_offset + 1)
    else:
        log.exception(label, stack_offset=stack_offset + 1)


def safe_run(target, args=None, kwargs=None, label='', warn=False,
             custom_exception=_DefaultException, custom_handler=None, stack_offset=0):
    try:
        return target(*(args or []), **(kwargs or {}))
    except custom_exception as e:
        return custom_handler(e, label)
    except MycroftException as e:
        _log_exception(label, e, warn or not e.stack_trace, stack_offset + 1)
    except Exception as e:
        _log_exception(label, e, warn, stack_offset + 1)
    return None


def warn_once(key, message, stack_offset=0):
    if key not in warned_keys:
        warned_keys.add(key)
        log.warning(message, stack_offset=stack_offset + 1)


warned_keys = set()


def flattened_values(dictionary):
    for k, v in dictionary.items():
        if isinstance(v, dict):
            for i in flattened_values(v):
                yield i
        else:
            yield v


def recursive_merge(a, b):
    """
    Returns generator for merged dict of a and b
    Usage:
        >>> dict(recursive_merge({'a': {'b': 2}}, {'a': {'c': 3}}))
        {'a': {'c': 3, 'b': 2}}
    """
    for k in set(a.keys()) | set(b.keys()):
        if k in a and k in b:
            if isinstance(a[k], dict) and isinstance(b[k], dict):
                yield k, dict(recursive_merge(a[k], b[k]))
            else:
                yield k, b[k]
        elif k in a:
            yield k, a[k]
        else:
            yield k, b[k]


def calc_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download(url, file: Union[str, io, None] = None, debug=True, timeout=None) -> Union[bytes,
                                                                                        None]:
    """Pass file as a filename, open file object, or None to return the request bytes"""
    if debug:
        log.debug('Downloading:', url)
    import urllib.request
    import shutil
    if isinstance(file, str):
        file = open(file, 'wb')
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if file:
                shutil.copyfileobj(response, file)
            else:
                return response.read()
    finally:
        if file:
            file.close()


def download_extract_tar(tar_url, folder, check_md5=False, subdir='',
                         on_update: Callable = None, on_complete: Callable = None) -> bool:
    """Warning! If check_md5 is True, it will delete <folder>/<subdir> when remote md5 updates"""
    data_file = join(folder, basename(tar_url))

    if not isdir(join(folder, subdir)):
        makedirs(folder, exist_ok=True)
        download(tar_url, data_file)

        import tarfile
        tar = tarfile.open(data_file)
        tar.extractall(path=folder)
        tar.close()
        return True
    elif check_md5:
        md5_url = tar_url + '.md5'
        try:
            remote_md5 = download(md5_url, debug=False, timeout=1).decode('ascii').split(' ')[0]
        except (RequestException, URLError) as e:
            log.warning('Failed to download md5 at url:', md5_url)
            return False
        if remote_md5 != calc_md5(data_file):
            on_update and on_update()
            rmtree(join(folder, subdir))
            download_extract_tar(tar_url, folder, subdir=subdir)
            on_complete and on_complete()
            return True
    return False
