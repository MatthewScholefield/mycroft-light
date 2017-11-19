from difflib import SequenceMatcher
from time import sleep

import psutil

from mycroft import MycroftSkill
from twiggy import log


class SystemStatusSkill(MycroftSkill):
    def __init__(self):
        super().__init__()
        def mkmethod(i):
            return lambda: self.add_memory_result(i, getattr(psutil.virtual_memory(), i))
        for i in ['free',  'used', 'total']:
            self.register_intent('mem.' + i, mkmethod(i))
        self.register_intent('mem.max.process', self.max_mem)
        self.register_intent('mem.usage.application', self.app_mem)
        self.register_intent('cpu.total.usage', self.total_cpu)
        self.register_intent('cpu.max.process', self.max_cpu)
        self.register_intent('cpu.usage.application', self.app_cpu)

    @staticmethod
    def format_kb(amount):
        gb = amount / (1024 * 1024 * 1024)
        if gb > 1.0:
            return round(gb, 1), 'GB', 'Gigabytes'
        else:
            return round(gb * 1024), 'MB', 'Megabytes'

    def add_memory_result(self, prefix, bytes):
        num, short, long = self.format_kb(bytes)
        self.add_result(prefix + '_short', str(num) + ' ' + short)
        self.add_result(prefix + '_long', str(num) + ' ' + long)

    def total_cpu(self):
        self.add_result('percent', psutil.cpu_percent(0.2))

    def max_mem(self):
        p = max(list(psutil.process_iter()), key=lambda x: x.memory_info_ex()[0])

        self.add_result('name', p.name())
        self.add_result('command', ' '.join(p.cmdline()))
        self.add_result('percent', p.memory_percent())
        self.add_memory_result('used', p.memory_info_ex()[0])

    @staticmethod
    def find_process(name):
        """Returns confidence, process"""
        name = name.lower()
        for i in psutil.process_iter():
            if i.name() in name or name in i.name():
                return SequenceMatcher(name, i.name()).ratio(), i
        return 0.0, None

    def app_mem(self, data):
        conf, p = self.find_process(data.matches['application'])
        if p:
            self.add_result('name', p.name())
            self.add_result('command', ' '.join(p.cmdline()))
            self.add_memory_result('used', p.memory_info_ex()[0])
        else:
            self.add_result('app', data.matches['application'])
            self.set_action('app.not.found')
        return 0.6 + 0.4 * conf

    def max_cpu(self):
        processes = list(psutil.process_iter())
        for i in processes:
            i.cpu_percent()
        sleep(0.2)
        usages = [i.cpu_percent() for i in processes]
        percent = max(usages)
        name = processes[usages.index(percent)].name()

        self.add_result('name', name)
        self.add_result('percent', percent)

    def app_cpu(self, data):
        conf, p = self.find_process(data.matches['application'])
        if p:
            self.add_result('name', p.name())
            self.add_result('command', ' '.join(p.cmdline()))
            self.add_result('percent', p.cpu_percent(0.2))
        else:
            self.add_result('app', p.name())
            self.set_action('app.not.found')
        return 0.6 + 0.4 * conf
