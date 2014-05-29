# -*- coding: utf-8 -*-
import config
import pymongo
from collections import Counter

db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_docs = db['docs']
co_pats = db['pats']
co_lexicon = db['lexicon']

emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}, {'_id':0, 'emotion':1})])

patCount = {}


# calculate occurrences of patterns
def count_patterns():

	global patCount

	for e in emotions:
		patCount[e] = Counter()
		for _doc in co_docs.find( { 'emotion': e, 'ldocID': {'$lt': 800}} ):
			_udocID = _doc['udocID']
			mdocs = list( co_pats.find( {'udocID': _udocID} ) )
			for mdoc in mdocs:
				patCount[e][mdoc['pattern'].lower()] += 1


# build lexicon storing pattern occurrence
def build_lexicon(patCount):
	for e in emotions:
		for p in patCount[e].keys():
			co_lexicon.insert( { 'pattern': p, 'emotion': e, 'count': patCount[e][p] } )

if __name__ == '__main__':

	count_patterns()
