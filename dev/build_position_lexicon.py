# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

import config, color
import pymongo
from collections import Counter

db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_docs = db['docs']
co_pats = db['pats']
co_lexicon_begin  = db['lexicon.nested.position.begin']
co_lexicon_middle = db['lexicon.nested.position.middle']
co_lexicon_end    = db['lexicon.nested.position.end']


