#!/usr/bin/python

# author:       Luca Soldaini
# email:        luca@soldaini.net
# description:  Importer class for concepts

# default modules
import codecs

# installed modules
# no modules

# project modules
# no modules



class AbstractConceptImporter(object):
    """Abstract class for concept importer"""
    def __init__(self):
        super(AbstractConceptImporter, self).__init__()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """Yeilds one concept"""
        raise NotImplementedError()


class ConceptImporterFromRRF(AbstractConceptImporter):
    """docstring for ConceptImporterFromRRF"""
    def __init__(self, mrconso_filepath, mrconso_schema=None):
        super(ConceptImporterFromRRF, self).__init__()
        self.filepath = mrconso_filepath


        u = lambda s: s.decode('utf-8')

        # uses the current MRCONSO schema if not provided
        if mrconso_schema is None:
            mrconso_schema = [('CUI', u), ('LAT', u),
                ('TS', lambda x: True if x.lower() == 'p' else False),
                ('LUI', u), ('STT', u), ('SUI', u),
                ('ISPREF', lambda x: True if x.lower() == 'y' else False),
                ('AUI', u), ('SAUI', u), ('SCUI', u),
                ('SDUI', u), ('SAB', u), ('TTY', u),
                ('CODE', u), ('STR', u), ('SRL', int),
                ('SUPPRESS', u), ('CFV', int)]

        self.schema = mrconso_schema

        self.__file = None

    def __open(self):
        self.__file = codecs.open(self.filepath)

    def next(self):
        if self.__file is None:
            self.__open()

        raw = self.__file.readline().strip().split('|')

        if raw == '':
            raise StopIteration

        # applies the function specified in the schema to the row
        parsed = {k: func(ln) if len(ln) > 0 else None
                  for (k, func), ln in zip(self.schema, raw)}

        return parsed

class ElasticSearchScoller(ConceptImporterFromRRF):
    def __init__(self, mrconso_filepath, index, doc_type,
                 mrconso_schema=None, demo=None, notifiy_every=0):
        super(ElasticSearchScoller, self).__init__(mrconso_filepath,
                                                   mrconso_schema)
        self.index = index
        self.doc_type = doc_type

        # for testing purposes only. when it reaches 0 (if not none)
        # iterator raises StopIteration
        self.__demo = int(demo) if demo is not None else demo
        self.__cnt = 0
        self.notifiy_every = notifiy_every

    def next(self):

        if self.__demo is not None:
            if self.__demo > 0:
                self.__demo -= 1
            else:
                raise StopIteration

        error = True
        while error:
            row = super(ElasticSearchScoller, self).next()
            try:
                doc = {
                    '_index': self.index,
                    '_type': self.doc_type,
                    '_id': row['AUI'],
                    '_source': {
                        'text': row['STR'],
                        'ngrams': row['STR'],
                        'AUI': row['AUI'],
                        'CUI': row['CUI'],
                        'SUI': row['SUI']
                        }
                }
                error = False
            except KeyError:
                print '[error] could not parse "{}"'.format(str(row))

        self.__cnt += 1
        if self.notifiy_every > 0 and self.__cnt % self.notifiy_every == 0:
            print '[info] {} served'.format(self.__cnt)

        return doc
