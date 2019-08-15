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
import time
from threading import Thread
from typing import Any, Dict, List, Union, Callable

from mycroft.util import log
from mycroft.util.misc import safe_run, _DefaultException


def run_ordered_parallel(items, get_function, args, kwargs,
                         order=None, daemon=False, label='', warn=False,
                         custom_exception=None, custom_handler=None, timeout=None) \
        -> Union[List[Any], Dict[str, Thread]]:
    order = order or []
    if '*' not in order:
        order.append('*')
    if daemon and timeout is None:
        timeout = 0.0
    return_vals = []

    def run_item(item, name):
        return_val = safe_run(get_function(item), args=args, kwargs=kwargs,
                              label=label + ' ' + name, warn=warn,
                              custom_exception=custom_exception, custom_handler=custom_handler)
        return_vals.append(return_val)

    threads = {}
    for name in set(items) - set(order):
        threads[name] = Thread(target=run_item, args=(items[name], name), daemon=daemon)

    for name in order:
        if name == '*':
            for i in threads.values():
                i.start()
            try:
                join_threads(threads.values(), timeout)
            except KeyboardInterrupt:
                log.error('KeyboardInterrupt joining threads:', [
                    name for name, t in threads.items() if t.is_alive()
                ])
                raise
        elif name in items:
            run_item(items[name], name)
        else:
            log.warning('Plugin from runner load order not found:', name)

    if not daemon:
        return return_vals
    return threads


def join_threads(threads, timeout: float = None) -> bool:
    """Join multiple threads, providing a global timeout"""
    if timeout is None:
        for i in threads:
            i.join()
        return True

    end_time = time.time() + timeout
    for i in threads:
        time_left = end_time - time.time()
        if time_left <= 0:
            return False
        i.join(time_left)
    return True


def run_parallel(functions: List[Callable], label='',
                 filter_none=False, *safe_args, **safe_kwargs) -> List[Union[Any, None]]:
    """
    Run a list of functions in parallel and return results

    Args:
        functions: all functions to be called
        label: label to prepend to all error messages
        filter_none: whether to remove None from return value list
        *safe_args: All other arguments forwarded to <safe_run>
    """
    threads = []
    return_vals = [None] * len(functions)
    for i, fn in enumerate(functions):
        def wrapper(i, fn=fn):
            fn_label = label + ' - ' + fn.__name__
            return_vals[i] = safe_run(fn, label=fn_label, *safe_args, **safe_kwargs)

        threads.append(Thread(target=wrapper, args=(i,)))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    if filter_none:
        return_vals = [i for i in return_vals if i]

    return return_vals
