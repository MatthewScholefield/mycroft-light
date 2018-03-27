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
from collections import namedtuple
from inspect import isclass
from typing import Union, Any, Callable, Dict

from mycroft.group_plugin import Empty
from mycroft.intent_match import IntentMatch
from mycroft.util.misc import warn_once, recursive_merge


class BoolAttr:
    def __init__(self, default=False):
        self.value = default

    def __call__(self, value=True):
        self.value = value

    def __bool__(self):
        return self.value

    def __repr__(self):
        return 'BoolAttr(%s)' % self.value


class Package:
    """
    Object to store skill interaction data
    Example Usage:
    >>> p = Package({
        ...     'faceplate': {
        ...         'mouth': {
        ...             'text': str
        ...         },
        ...         'eyes': {
        ...             'color': (int, int, int),
        ...         }
        ...     }
        ... })
        ...
        >>> p.faceplate.mouth.text = 'hello'
        >>> p.faceplate.eyes.color = (0, 255, 100)
        >>> print(p)

        faceplate:
            mouth:
                text: 'hello'
            eyes:
                color: (0, 255, 100)
        >>> p.execute({
        ...     'faceplate': {
        ...         'mouth': {
        ...             'text': lambda x: print('Setting the faceplate text to:', x)
        ...         },
        ...         'eyes': {
        ...             'color': lambda colors: print('Setting the eye color to:', colors)
        ...         }
        ...     }
        ... })
        ...
        Setting the faceplate text to: hello
        Setting the eye color to: (0, 255, 100)
    """
    def __init__(self, struct: dict=None):
        self._struct = struct or {}
        self._load_struct(self._struct)

    def __type_hinting__(self):
        self.action = ''  # type: str
        self.skip_activation = ''  # type: bool
        self.faceplate = ''  # type: namedtuple('Faceplate', 'eyes mouth')
        self.data = ''  # type: dict
        self.skill = ''  # type: str
        self.lang = ''  # type: str
        self.match = ''  # type: IntentMatch
        self.confidence = ''  # type: str

    def _load_struct(self, struct: dict):
        if not isinstance(struct, dict):
            raise ValueError('Invalid struct: ' + str(struct))
        for key, value in struct.items():
            if key in self.__dict__:
                self._verify_assignment(key, self.__dict__[key])
                continue

            if isinstance(value, dict):
                self.__dict__[key] = Package(value)
            elif value == ():
                self.__dict__[key] = BoolAttr()
            else:
                self.__dict__[key] = None

    def add(self, struct: dict):
        self._load_struct(struct)
        self._struct = dict(recursive_merge(self._struct, struct))

    @classmethod
    def get_type(cls, obj):
        if isinstance(obj, (list, set, tuple)):
            return type(obj)(map(cls.get_type, obj))
        return type(obj)

    def _verify_assignment(self, key, value):
        """Checks types according to values defined in the package structure"""
        if value is None:
            return

        if key not in self._struct:
            message = 'Setting nonexistent attribute, ' + key + ', to ' + str(value)
            warn_once(type(self).__name__ + key, message, stack_offset=2)
            return

        desc = self._struct[key]

        if isinstance(desc, dict):
            raise AttributeError(key + ' must be followed by one of: ' + str(list(desc)))

        if desc == ():
            raise AttributeError('This should be called like: ' + key + '()')

        if isinstance(desc, (list, set, tuple)) and len(desc) > 0 and not isclass(list(desc)[0]):
            if value not in desc:
                raise TypeError(value + ' must be one of the following values: ' + str(list(desc)))
        else:
            value_typ = self.get_type(value)
            if desc != value_typ:
                raise TypeError('Cannot assign value ' + str(value) + ' to type ' + desc.__name__)

    def __setattr__(self, key, value):
        if key.startswith('_') or key in ('rt', 'config'):
            return object.__setattr__(self, key, value)

        self._verify_assignment(key, value)
        self.__dict__[key] = value

    def __getattr__(self, item):
        try:
            return self.__dict__[item]
        except KeyError:
            if item.startswith('_'):
                raise AttributeError
            warn_once((type(self).__name__, item), 'package.' + item + ' attribute not found',
                      stack_offset=1)
            return Empty()

    @staticmethod
    def _to_str(cls, obj, indent=4, indent_level=0):
        """Show visual tree of attributes"""
        if not isinstance(obj, cls):
            def format_iter(x):
                return ', '.join(formatters.get(type(i), repr)(i) for i in x)
            formatters = {
                tuple: lambda x: '(' + format_iter(x) + ')',
                set: lambda x: 'set(' + format_iter(x) + ')',
                list: lambda x: '[' + format_iter(x) + ']',
                type: lambda x: x.__name__,
                BoolAttr: lambda x: 'True' if x else '',
                type(None): lambda _: ''
            }
            return formatters.get(type(obj), repr)(obj) + '\n'
        s = '\n'
        for key, value in sorted(obj.items(), key=lambda k_v: ('zzz' + k_v[0]) if isinstance(k_v[1], cls) else k_v[0]):
            if key.startswith('_') or not value:
                continue
            value_str = Package._to_str(cls, value, indent, indent_level + 1)
            s += ' ' * indent * indent_level + str(key) + ': ' + value_str
        return s

    def render_structure(self):
        return self._to_str(dict, self._struct)

    def __repr__(self):
        return self._to_str(type(self), self)

    def items(self):
        for key, value in self.__dict__.items():
            if key.startswith('_') or not value:
                continue
            if isinstance(value, Package):
                yield key, dict(value.items())
            else:
                yield key, value

    def __bool__(self):
        for key, value in self.__dict__.items():
            if key.startswith('_') or not value:
                continue
            if value:
                return True
        return False

    @classmethod
    def execute_data(cls, data: Union[Dict, Any], handlers: Union[Dict, Callable]):
        """
        Pairs a dict of handlers with the package's data.
        For example usage see the constructor for this class
        """
        if callable(handlers):
            return handlers(data)

        results = {}

        for key, value in data:
            if key not in handlers or not value:
                continue
            results[key] = cls.execute_data(value, handlers[key])

        return results

    def execute(self, handlers: Dict):
        return self.execute_data(self, handlers)
