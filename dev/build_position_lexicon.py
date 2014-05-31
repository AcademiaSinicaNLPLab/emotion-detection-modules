# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

import config, color
import pymongo
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_emotions = db[config.co_emotions_name]
co_docs = db[config.co_docs_name]
co_sents = db[config.co_sents_name]
co_pats = db[config.co_pats_name]
co_lexicon = db['lexicon.nested.position']

config.begPercentage = 20
config.midPercentage = 60
config.endPercentage = 20

position = 'end' # default position

def counting():

	pat_counts = {
		'beginning': defaultdict(Counter),
		'middle': defaultdict(Counter),
		'end': defaultdict(Counter)
	}

	## given a doc
	for doc in co_docs.find({'ldocID' : {'$lt': 800}}):
		# udocID = 38000
		
		udocID = doc['udocID']
		emotion = doc['emotion']

		# get all sents, and count words
		sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
		usentID_offset = min(sents)
		total_words = sum([sents[x] for x in sents])

		# calculate thresholds
		th1 = total_words * config.begPercentage/float(100)
		th2 = total_words * (config.begPercentage+config.midPercentage)/float(100)

		## get all pats in curernt doct
		for pat in co_pats.find( {'udocID': udocID} ):
			lanchorID = sum([sents[usentID_offset+i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
			if lanchorID <= th1: 
				position = 'beginning'
			elif lanchorID <= th2: 
				position = 'middle'
			else: 
				position = 'end'

			pat_counts[position][pat['pattern'].lower()][emotion] += 1
	return pat_counts

def build(pat_counts):
	for position in pat_counts:
		for pat in pat_counts[position]:
			mdoc = {
				'pattern': pat,
				'count': pat_counts[position][pat],
				'position': position
			}
			co_lexicon.insert(mdoc)

	co_lexicon.create_index([('pattern', pymongo.ASCENDING), ('position', pymongo.ASCENDING)])


def check(drop):
	lexicon_size = co_lexicon.count()
	if lexicon_size > 0 and drop:
		print 'drop current lexicon with size', lexicon_size, '? [y/N]',
		yn = raw_input().strip()
		if yn.lower() == 'y':
			co_lexicon.drop()
		else:
			print "use python build_position_lexicon.py [drop/flush] to flush old lexicon"
			exit(0)
	else:
		print "use python build_position_lexicon.py [drop/flush] to flush old lexicon"
		exit(0)

if __name__ == '__main__':

	drop = False
	if len(sys.argv) > 1: drop = True if sys.argv[1].strip().replace('-','') in ['drop', 'flush','force','f'] else False

	check(drop)

	print 'counting patterns'
	pat_counts = counting()

	print 'building lexicon'
	build(pat_counts)








