#!/usr/bin/python

# author:       Luca Soldaini
# email:        luca@soldaini.net
# description:  Bunch of utils that might be useful

# default modules
from __future__ import print_function
import errno

import random
import hashlib
import copy
import os
import sys
import shelve
import string
import traceback
from itertools import tee, izip
from subprocess import Popen, PIPE
from functools import wraps
from collections import OrderedDict
from optparse import OptionParser
from time import time as now

# installed modules
from scipy.stats import entropy
from numpy.linalg import norm
import numpy as np

# project modules
# no modules

def cls_decorate_all(decorator, exclude=None):
    """Decorate all methods in class except those in exclude"""

    if exclude is None:
        exclude = set()

    if not callable(exclude):
        exclude_func = lambda e: e in exclude
    else:
        exclude_func = exclude

    def wrapper(cls):
        for attr in cls.__dict__:
            mthd = getattr(cls, attr)
            if callable(mthd) and not exclude_func(attr):
                setattr(cls, attr, decorator(mthd))
        return cls
    return wrapper


def error_wrapper_pool(method):
    """ Make sure that your multiprocessing pool workers report
        their full traceback when crashing.
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        try:
            resp = method(*args, **kwargs)
        except:
            trace = traceback.format_exception(*sys.exc_info())
            raise RuntimeError(''.join(trace))
        return resp
    return wrapper


def fmap(fn_list, arg):
    """Iteratively applies the functions in fn_list to argument arg"""
    return reduce(lambda arg, fn: fn(arg), fn_list, arg)


def JSD(P, Q):
    """Implementation of the [Jensen-Shannon divergence metric]
    (https://en.wikipedia.org/wiki/Jensen%E2%80%93Shannon_divergence)
    from http://stackoverflow.com/a/27432724"""
    _P = P / norm(P, ord=1)
    _Q = Q / norm(Q, ord=1)
    _M = 0.5 * (_P + _Q)
    return 0.5 * (entropy(_P, _M) + entropy(_Q, _M))


class Bunch(dict):
    """Collect elements in a bunch"""
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def __copy__(self):
        return Bunch({k: v for k, v in self.__dict__.iteritems()})

    def __deepcopy__(self, memodict=None):
        return Bunch({k: copy.deepcopy(v, memodict)
                     for k, v in self.__dict__.iteritems()})


def randstr(N):
    """generates a random string of length N
    from http://stackoverflow.com/a/23728630
    """
    vals = string.ascii_uppercase + string.digits
    s = ''.join(random.SystemRandom().choice(vals) for i in range(N))
    return s


def merge_dicts(a, b, path=None):
    """recursively merges b into a;
    from http://stackoverflow.com/a/7205107"""
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def make_stratified_folds(data, k=10, key=None, seed=None):
    """Make stratified fold of data.
    By default, 10 folds are created, and the elements itself are used as
    keys to ensure stratification.

    Args:
        data (list): the data to stratify
        k (int, default=10): the numbers of fold to create
        key (func, default=None): the key to extract the label used to
            determine stratification.

    Returns:
        folds (generator): a generator yielding two generators, one for
            training data, one for testing data.
    """
    if key is None:
        key = lambda e: e

    seed_func = ((lambda: random.random()) if seed is None
                 else (lambda: seed))

    cnt = {}
    map(lambda (i, e): cnt.setdefault(key(e), []).append(i), enumerate(data))

    folds_ids = [[] for _ in range(k)]
    for i, ids in enumerate(cnt.itervalues()):
        random.shuffle(ids, seed_func)

        # the offset i ensures that one fold is not constantly the smallest
        # in case the size of data is not divisible by the number of folds
        map(lambda (j, _id): folds_ids[(i + j) % k].append(_id),
            enumerate(ids))

    # return a generator of folds containing two generators of training
    # and test sets to prevent
    folds = (((elem for i, elem in enumerate(data) if i not in fold),
              (elem for i, elem in enumerate(data) if i in fold))
             for fold in folds_ids)

    return folds



def process_call(cmd):
    """execute proces call specified in list cmd"""
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    msg_out, msg_err = proc.communicate()
    msg_err = '\n'.join([e for e in msg_err.split('\n')
                         if e.find('loading') < 0])
    if msg_err:
        err_msg = ('subprocess exited with error \n"%s"' %
                   '\n'.join(['\t%s' % l
                              for l in msg_err.split('\n')]))
        raise IOError(err_msg)

    return msg_out


class LimitedSizeDict(OrderedDict):
    """ Size-bounded dicitonary with LRU policy.
        From http://stackoverflow.com/questions/2437617
    """
    def __init__(self, *args, **kwargs):
        self.size_limit = kwargs.pop("size_limit", None)
        OrderedDict.__init__(self, *args, **kwargs)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)

def flatten(l):
    ''' flatten a list of lists into a single list
        from http://stackoverflow.com/questions/11264684/'''
    return [val for subl in l for val in subl]


def shift_bk(li, n):
    """Return a copy of li shifted backwards by n positions"""
    return li[n:] + li[:n]


def shift_fw(li, n):
    """Return a copy of li shifted fowards by n positions"""
    return li[-n:] + li[:-n]


def hash_obj(obj):
    """Returs weak hash for object obj"""
    try:
        return hashlib.md5(json.dumps(obj)).hexdigest()
    except TypeError:
        pass

    if type(obj) is dict:
        outobj = {}
        for k, v in obj.iteritems():
            try:
                outobj[k] = json.dumps(v)
            except TypeError:
                pass
    elif type(obj) in (list, tuple, set):
        outobj = []
        for v in obj:
            try:
                outobj.append(json.dumps(v))
            except TypeError:
                pass
    else:
        raise RuntimeError('[error] obj can not be hashed')

    return hashlib.md5(json.dumps(outobj)).hexdigest()


def mkdir_p(path):
    ''' from http://stackoverflow.com/questions/600268'''
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."

    next(b, None)



def timer(func):
    """Times function func"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from itertools import tee, izip
        printer = kwargs.pop('printer', print)
        comment = kwargs.pop('comment', '')
        from itertools import tee, izip
        mthdname = kwargs.pop('mthdname', True)

        start = now()
        resp = func(*args, **kwargs)
        elapsed = now() - start
        if elapsed > 3600:
            timestr = ('{:02.0f}:{:02.0f}:{:05.2f}'
                       '').format(elapsed / 3600,
                                  (elapsed % 3600) / 60,
                                  elapsed % 60)
        elif elapsed > 60:
            timestr = ('{:02.0f}:{:05.2f}'
                       '').format((elapsed % 3600) / 60,
                                  elapsed % 60)
        else:
            timestr = ('{:.3f} s'.format(elapsed))
        printer('[timer] %s%s executed in %s' %
                (func.__name__ if mthdname else '',
                 (' (%s)' % comment if comment else ''),
                 timestr))
        return resp
    return wrapper


def list_powerset(lst, include_empty=True):
    """ Creates the powerset of list lst
    from http://rosettacode.org/wiki/Power_set#Python"""
    # the power set of the empty set has one element, the empty set
    result = [[]]

    for x in lst:
        # for every additional element in our set
        # the power set consists of the subsets that don't
        # contain this element (just take the previous power set)
        # plus the subsets that do contain the element (use list
        # comprehension to add [x] onto everything in the
        # previous power set)
        result.extend([subset + [x] for subset in result])

    if not include_empty:
        result.remove([])

    return result


def contains_sublist(lst, sublst):
    ''' from http://stackoverflow.com/questions/3313590/'''
    n = len(sublst)
    return any((sublst == lst[i:i + n]) for i in xrange(len(lst) - n + 1))


def normalize_dictlist(obj_list, fields, new_field=False,
                       new_field_names=None, sum_to_1=False):
    '''Gets list of dictionaries (obj_list) and normalizes the values
     in obj[fields[i]], returns a dictionary with the
    same field normalized if
    new_field is false, if new_field is True, then adds
    a new field to the dicitonary with name new_field_name
    that contains normalized data'''
    for idx, fl in enumerate(fields):
        min_val = min(obj_list, key=lambda x: x[fl])[fl]
        max_val = max(obj_list, key=lambda x: x[fl])[fl]
        if sum_to_1:
            sum_val = sum(item[fl] for item in obj_list)
        new_list = []
        for obj in obj_list:
            if not new_field:
                if sum_to_1:
                    obj[fl] = obj[fl] / float(sum_val)
                else:
                    obj[fl] = (obj[fl] - min_val) / float(
                        max_val - min_val)

            else:
                if sum_to_1:
                    obj[new_field_names[idx]] = obj[fl] / float(sum_val)
                else:
                    obj[new_field_names[idx]] = (obj[fl] - min_val) / float(
                        max_val - min_val)

            new_list.append(obj)
    return new_list


class VerbosePrinter(object):
    """Printer that prints only when verbose is on"""

    def __init__(self, enabled=False, prefix=None, file_print=None):
        if file_print is None:
            file_print = sys.stdout
        self.file_print = file_print

        if prefix:
            self.prefix = '[{0}] '.format(prefix)
        else:
            self.prefix = False

        self.enabled = enabled

    def __call__(self, message, sep=' ', end='\n'):

        if self.enabled:
            if self.prefix:
                print('{p}{msg}'.format(p=self.prefix, msg=message),
                      sep=sep, end=end, file=self.file_print)
            else:
                print(message, sep=sep, end=end, file=self.file_print)
