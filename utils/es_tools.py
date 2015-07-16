#!/usr/bin/python

# author:       Luca Soldaini
# email:        luca@soldaini.net
# description:  Tools for elasticsearch api

# default modules
from functools import wraps

# installed modules
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.client import IndicesClient

# project modules
from utils.common import cls_decorate_all


# def connect(host, port, index=None, username=None, password=None):
#     """Connect ot elasticsearch instance"""
#     def index_decorator(method):
#         @wraps(method)
#         def wrapper(*args, **kwargs):
#             kwargs['index'] = index
#             # print args, kwargs, method
#             return method(*args, **kwargs)
#         return wrapper

#     exclude = set(['ping', 'info', 'get_template', 'get_script',
#                    'clear_scroll', 'delete_script', 'delete_template',
#                    'get_template', 'put_script', 'put_template', 'scroll'])
#     exclude_func = lambda m: m.startswith('__') or m in exclude

#     if index is not None:
#         ES = cls_decorate_all(index_decorator, exclude_func)(Elasticsearch)
#     else:
#         ES = Elasticsearch

def connect(host, port, index=None, username=None, password=None):
    # sets up kwargs
    kwargs = {'host': host, 'port': port}
    if username is not None and password is not None:
        kwargs['http_auth'] = '{}:{}'.format(username, password)

    return Elasticsearch(**kwargs)

def create_index(index, mapping,
                 host, port, username=None, password=None):
    es = connect(host, port, username=username, password=password)
    ic = IndicesClient(es)

    create = True
    if ic.exists(index):
        resp = None
        msg = 'index "{}" exists. overwrite? yes/[no]: '.format(index)
        while resp != 'yes' and resp != 'no':
            resp = raw_input(msg).strip().lower()
            resp = 'no' if not resp else resp
            msg = 'please type "yes" or "no": '

        if resp == "yes": ic.delete(index)
        else: create = False

    if create:
        ic.create(index=index, body=mapping)


def bulk_create(client, docs, chunk_size=1000):
    resp = bulk(client, docs, chunk_size=chunk_size)
    return resp[0]
