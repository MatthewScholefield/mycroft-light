import inspect
from inspect import isclass
from os import chdir, makedirs
from os.path import realpath, dirname
from subprocess import check_output
from typing import Set

from mycroft.group_plugin import GroupPlugin, GroupRunner
from mycroft.option_plugin import OptionPlugin
from mycroft.util import log


def get_visible(obj):
    return filter(lambda x: not x.startswith('_'), dir(obj))


def tree_default(parents, obj):
    tree = {}
    for attr in get_visible(obj):
        tree[attr] = calc_tree(parents, getattr(obj, attr))
    if tree == {}:
        return get_info(obj)
    return tree


def tree_dict(parents, obj):
    tree = {'<dict>': ''}
    for i in get_visible(obj):
        attr = getattr(obj, i)
        if i in dir(dict):
            continue
        tree[i] = calc_tree(parents, attr)
    return tree


def tree_group_runner(parents, obj):
    tree = {}
    for name in get_visible(obj.cls):
        attr = getattr(obj.cls, name)
        if not callable(attr):
            continue
        tree[name] = calc_tree(parents, attr)
    if tree == {}:
        return get_info(obj)
    return tree


def tree_option_plugin(parents, obj):
    return calc_tree(parents, obj._plugin)


def tree_group_plugin(parents, obj):
    subtrees = list(obj)
    tree = {}
    for i in subtrees:
        tree[i] = calc_tree(parents, obj[i])
    tree.update(tree_default(parents, obj))
    return tree


def get_info(obj):
    try:
        lines = inspect.getsource(obj).split('\n')
        lines = [i for i in lines if '@' not in i]  # filter out decorators
        return lines[0].replace('def ', '').replace('):', ')').replace('  ', '').replace(
            obj.__name__, '').replace('self, ', '').replace('self', '')
    except Exception:
        return None


def calc_tree(parents: Set[int], obj):
    """
    Calculates a json object representing all callable attributes of an object
    Each key represents another attribute and each value is either:
     - Another dictionary with sub-attributes
     - A string containing the function definition

    Args:
        parents: Set of all memory ids of parent objects
                 This prevents infinite recursion
        obj:     Python object to recursively look for callable attributes in

    Returns:
        dict or str: dict of all callable attributes or
                     a string to indicate there are none
    """
    if id(obj) in parents:
        return '...'
    try:
        mod = object.__getattribute__(obj, '__module__')
        base = mod.split('.')[0]
        if base != 'mycroft':
            if not check_output(
                    ['find', dirname(dirname(realpath(__file__))), '-name', base + '.py']):
                return get_info(obj)
            else:
                log.debug(mod, base, obj)
    except AttributeError:
        return get_info(obj)
    obj_cls = obj if isclass(obj) else type(obj)
    for cls, handler in [
        (GroupRunner, tree_group_runner),
        (GroupPlugin, tree_group_plugin),
        (OptionPlugin, tree_option_plugin),
        (dict, tree_dict),
        (object, tree_default)
    ]:
        if issubclass(obj_cls, cls):
            return handler(parents | {id(obj)}, obj)
    raise ValueError


def make_dir_tree(tree):
    """
    Writes a dict tree of attributes to a series of folders and empty files
    This can be used in conjunction with the `tree` linux command as a
    hackish way of generating a nice diagram of attributes
    """
    for name, value in tree.items():
        if isinstance(value, dict):
            makedirs(x, exist_ok=True)
            chdir(name)
            make_dir_tree(value)
            chdir('..')
        else:
            if value is None or value == '...':
                continue
            with open(name + value, 'w') as f:
                f.write('')
