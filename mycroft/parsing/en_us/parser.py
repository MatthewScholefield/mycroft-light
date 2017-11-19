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

import re
from difflib import SequenceMatcher

from mycroft.parsing.mycroft_parser import MycroftParser, TimeType


class Parser(MycroftParser):
    """Helper class to parse common parameters like duration out of strings"""

    def __init__(self):
        self.units = [
            ('one', '1'),
            ('two', '2'),
            ('three', '3'),
            ('four', '4'),
            ('five', '5'),
            ('size', '6'),
            ('seven', '7'),
            ('eight', '8'),
            ('nine', '9'),
            ('ten', '10'),
            ('eleven', '11'),
            ('twelve', '12'),
            ('thir', '3.'),
            ('for', '4.'),
            ('fif', '5.'),
            ('teen', '+10'),
            ('ty', '*10'),
            ('hundred', '* 100'),
            ('thousand', '* 1000'),
            ('million', '* 1000000'),
            ('and', '_+_')
        ]
        self.ttype_names_s = {
            TimeType.SEC: ['second', 'sec', 's'],
            TimeType.MIN: ['minute', 'min', 'm'],
            TimeType.HR: ['hour', 'hr', 'h'],
            TimeType.DAY: ['day', 'dy', 'd']
        }

        units = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen",
        ]

        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty",
                "ninety"]

        scales = ["hundred", "thousand", "million", "billion", "trillion"]

        self.numwords = {}
        self.numwords["and"] = (1, 0)
        for idx, word in enumerate(units):
            self.numwords[word] = (1, idx)
        for idx, word in enumerate(tens):
            self.numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):
            self.numwords[word] = (10 ** (idx * 3 or 2), 0)

    def duration(self, string):
        regex_str = ('(((' + '|'.join(k for k, v in self.units) + r'|[0-9])+[ \-\t]*)+)(' +
                     '|'.join(name for ttype, names in self.ttype_names_s.items() for name in
                              names) + ')s?')
        dur = 0
        matches = tuple(re.finditer(regex_str, string))
        if len(matches) == 0:
            raise ValueError
        for m in matches:
            num_str = m.group(1)
            ttype_str = m.group(4)
            for ttype, names in self.ttype_names_s.items():
                if ttype_str in names:
                    ttype_typ = ttype
            num, conf = self.to_number(num_str)
            dur += ttype_typ.to_sec(num)
        return dur, conf

    def to_number(self, textnum):

        ordinal_words = {'first': 1, 'second': 2, 'third': 3, 'fifth': 5, 'eighth': 8,
                         'ninth': 9, 'twelfth': 12}
        ordinal_endings = [('ieth', 'y'), ('th', '')]

        textnum = textnum.replace('-', ' ')

        current = result = 0
        curstring = ""
        onnumber = False
        for word in textnum.split():
            if word in ordinal_words:
                scale, increment = (1, ordinal_words[word])
                current = current * scale + increment
                if scale > 100:
                    result += current
                    current = 0
                onnumber = True
            else:
                for ending, replacement in ordinal_endings:
                    if word.endswith(ending):
                        word = "%s%s" % (word[:-len(ending)], replacement)
                try:
                    num = float(word)
                    if num % 1 == 0:
                        num = int(num)
                except ValueError:
                    num = None

                if word not in self.numwords and num is None:
                    if onnumber:
                        curstring += repr(result + current) + " "
                    curstring += word + " "
                    result = current = 0
                    onnumber = False
                else:
                    if num is not None:
                        scale, increment = 1, num
                    else:
                        scale, increment = self.numwords[word]

                    current = current * scale + increment
                    if scale > 100:
                        result += current
                        current = 0
                    onnumber = True
            if onnumber:
                curstring += repr(result + current)
            return curstring

    def to_number(self, string):
        string = string.replace('-', ' ')  # forty-two -> forty two
        for unit, value in self.units:
            string = string.replace(unit, value)
        string = re.sub(r'([0-9]+)[ \t]*([\-+*/])[ \t]*([0-9+])', r'\1\2\3', string)

        regex_re = [
            (r'[0-9]+\.([^\-+*/])', r'a\1'),
            (r'\.([\-+*/])', r'\1'),
            (r' \* ', r'*'),
            (r' _\+_ ', r'+'),
            (r'([^0-9])\+[0-9]+', r'\1'),
            (r'([0-9]) ([0-9])', r'\1+\2'),
            (r'(^|[^0-9])[ \t]*[\-+*/][ \t]*', ''),
            (r'[ \t]*[\-+*/][ \t]*([^0-9]|$)', '')
        ]

        for sr, replace in regex_re:
            string = re.sub(sr, replace, string)

        num_strs = re.findall(r'[0-9\-+*/]+', string)
        if len(num_strs) == 0:
            raise ValueError

        num_str = max(num_strs, key=len)

        conf = SequenceMatcher(None, string.replace(' ', ''), num_str.replace(' ', '')).ratio()

        try:
            # WARNING Eval is evil; always filter string to only numbers and operators
            return eval(num_str), conf
        except SyntaxError:
            raise ValueError

    def format_quantities(self, quantities):
        complete_str = ', '.join(
            [str(amount) + ' ' + self.ttype_names_s[ttype][0] + ('s' if amount > 1 else '') for
             ttype, amount in quantities])
        complete_str = ' and '.join(complete_str.rsplit(', ', 1))
        return complete_str
