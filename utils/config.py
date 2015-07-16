#!/usr/bin/python

# author:       Luca Soldaini
# email:        luca@soldaini.net
# description:  parse a configuration file in JSON format

# default modules
import os
import ast
import sys
import json
import codecs
import hashlib
import numbers
from argparse import ArgumentParser
from functools import wraps
from collections import Sequence, Mapping
from copy import deepcopy

# installed modules
# no modules

# project modules
from utils import commentjson as json


def generate_config_cache_comment(ignore=None, include=None):
    """Automatically generate cache comment for a class method based on
    the config file in the cache file"""

    # they are out of scope in the wrapper
    dec_ignore = ignore
    dec_include = include

    def decorator(method):
        @wraps(method)
        def wrapper(*args, **kwargs):

            config = deepcopy(args[0].config)

            # include all the keys if no include is specified
            include = config.keys() if dec_include is None else dec_include

            ignore = dec_ignore if dec_ignore is not None else []

            # puts together keys to be removed
            to_remove = (filter(lambda k: k not in include, config.keys()) +
                         ignore)

            # removes keys not it include if include != None
            # and keys in ignore
            map(lambda k: config.pop(k), to_remove)

            data = hashlib.md5(json.dumps(repr(config))).hexdigest()

            kwargs['cache_comment'] = kwargs.pop('cache_comment', '') + data

            return method(*args, **kwargs)
        return wrapper
    return decorator

class BaseConfig(object):
    def __init__(self, current, default=None, parent=None):

        self.__parent = parent

        # loads default configuration
        if default is not None:
            config_default = self.__class__(default)
            self.update(config_default)

        if (isinstance(current, numbers.Number) or
                isinstance(current, basestring)):
            raise TypeError('Can\'t make Config from {}'
                            ''.format(type(current)))

        self.__parse__(current)

    @property
    def parent(self):
        return self.__parent


    def __hash__(self):
        data = json.dumps(eval(self.__repr__()))
        return int(hashlib.md5(data).hexdigest(), 16)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def copy(self):
        return deepcopy(self)


class ConfigList(BaseConfig, list):
    def __parse__(self, config_list):
        for e in config_list:
            if isinstance(e, Mapping):
                self.append(ConfigDict(e, parent=self))
            elif isinstance(e, list) or isinstance(e, tuple):
                self.append(ConfigList(e, parent=self))
            else:
                self.append(e)

    def __repr__(self):
        return str([e for e in self])

    def update(self, lst):
        while len(self) > 0: self.pop()
        self.extend(lst)


class ConfigDict(BaseConfig):
    def __parse__(self, config_dict):
        for k, v in config_dict.iteritems():

            # pull up existing dictionary or set it to empty
            # if it does not extist (e.g., we are not updating an
            # existing configuration
            existing = self.__dict__.get(k, {})

            if isinstance(v, Mapping):
                # value is a mapping (e.g., a dictionary)

                if len(set(v.keys()).difference(existing.keys())) > 0:
                    # if the keys in the new dictionary are not
                    # all part of the existing dictionary, then
                    # the existing dictionary is overridden by
                    # the new one
                    existing = None

                self.__dict__[k] = ConfigDict(v, default=existing, parent=self)

            elif isinstance(v, list) or isinstance(v, tuple):
                # value is a list/tuple
                self.__dict__[k] = ConfigList(v, parent=self)

            else:
                # value is a simple value
                self.__dict__[k] = v

    def __getitem__(self, key, default=None):
        args = [key, default] if default is not None else [key]
        return self.__dict__.get(*args)

    def update(self, other):
        return self.__dict__.update(other)

    def pop(self, key):
        return self.__dict__.pop(key)

    def iteritems(self):
        return ((k, v) for k, v in self.__dict__.iteritems()
                if not(k.startswith('_')))

    def iterkeys(self):
        return (k for k in self.__dict__.iterkeys()
                if not(k.startswith('_')))

    def itervalues(self):
        return (v for k, v in self.__dict__.iteritems()
                if not(k.startswith('_')))

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def __iter__(self):
        return self.iterkeys()

    def __repr__(self):
        args_it = ('{}: {}'.format(repr(k), repr(self.__dict__[k]))
                   for k in sorted(self.__dict__) if not(k.startswith('_')))
        s = '{{{}}}'.format(', '.join(args_it))
        return s


def Config(current, default=None):
    if default is not None and isinstance(default, basestring):
        with codecs.open(default, 'rb', 'utf-8') as f:
            default = json.load(f)

    if isinstance(current, basestring):
        with codecs.open(current, 'rb', 'utf-8') as f:
            current = json.load(f)

    if isinstance(current, Mapping):
        return ConfigDict(current, default)
    elif isinstance(v, list) or isinstance(v, tuple):
        return ConfigList(current, default)
    else:
        raise TypeError('Can\'t make Config from {}'.format(type(current)))


def parse_config(default_config):
    ag = ArgumentParser()
    ag.add_argument('-c', '--config', default=default_config)
    opts = ag.parse_args()

    try:
        # try to interpret opts.config as a json blob
        input_config = json.loads(opts.config)
    except ValueError:
        input_config = opts.config

    config = Config(input_config, default_config)

    return config
