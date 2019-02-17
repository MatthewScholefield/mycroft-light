import inspect
from threading import Timer
from typing import Callable

from mycroft.services.service_plugin import ServicePlugin
from mycroft.util.misc import safe_run


class SchedulerService(ServicePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        self.tasks = {}

    def _create_task(self, repeating, func, delay, name, args, kwargs, identifier):
        identifier = identifier or self._create_identifier(func.__name__)
        if identifier in self.tasks:
            self.tasks[identifier].cancel()
        t = self.tasks[identifier] = ScheduledTask(repeating, func, delay, name, args, kwargs)
        t.start()

    def _create_identifier(self, function_name):
        """Creates an identifier unique to the line that scheduled the function"""
        # Stack:
        # [0] - _create_identifier()
        # [1] - _create_task()
        # [1] - repeating() or once()
        # [2] - caller
        stack = inspect.stack()
        record = stack[2]
        mod = inspect.getmodule(record[0])
        module_name = mod.__name__ if mod else ''
        function_name = record[3]
        line_no = record[2]
        return function_name + '-' + module_name + ':' + function_name + ':' + str(line_no)

    def repeating(self, func: Callable, delay: int,
                  name='', args=None, kwargs=None, identifier=''):
        self._create_task(True, func, delay, name, args, kwargs, identifier)

    def once(self, func: Callable, delay: int,
             name='', args=None, kwargs=None, identifier=''):
        self._create_task(False, func, delay, name, args, kwargs, identifier)

    def cancel(self, identifier: str) -> bool:
        if identifier in self.tasks:
            self.tasks[identifier].cancel()
            del self.tasks[identifier]
            return True
        return False


class ScheduledTask:
    def __init__(self, repeating: bool, func: Callable, delay: int,
                 name='', args=None, kwargs=None):
        self.repeating = repeating
        self.func = func
        self.delay = delay
        self.name = name or func.__name__
        self.args = args or []
        self.kwargs = kwargs or {}
        self.is_running = True

        self.timer = None  # type: Timer

    def start(self):
        def wrapper():
            safe_run(self.func, args=self.args, kwargs=self.kwargs,
                     label='scheduled function ' + self.name)
            if self.repeating:
                self.start()

        self.timer = Timer(self.delay, wrapper)
        self.timer.start()

    def cancel(self):
        if self.timer:
            self.timer.cancel()
