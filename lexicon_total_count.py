# -*- coding: utf-8 -*-

import config
import os
import pymongo
import logging
import pickle
from collections import defaultdict, Counter

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# class TotalCount(object):
# 	"""docstring for TotalCount"""
# 	def __init__(self, arg):
# 		super(TotalCount, self).__init__()
# 		self.arg = arg
		
target_name = 'pattern'

# def create_lexicon_pattern_total_count(co_pats, co_dest, verbose=False):
def create_lexicon_pattern_total_count():
	co_pats = db[config.co_pats_name]
	co_dest = db[config.co_lexicon_pattern_tc_name]

	PatTC = defaultdict(Counter)
	for mdoc in co_pats.find():
		pat = mdoc['pattern'].lower()
		udocID = mdoc['udocID']
		PatTC[udocID][pat] += 1

	# co_dest = db[config.co_lexicon_pattern_tc_name]
	for udocID in PatTC:
		mdoc = { 'udocID': udocID, target_name: PatTC[udocID].items() }
		co_dest.insert(mdoc)
	co_dest.create_index('udocID')

def create_lexicon_pattern_position_total_count(co_pats, co_sents, co_docs, co_dest):
	
	PatTC = defaultdict(Counter)

	udocIDs = [ x['udocID'] for x in list( co_docs.find() ) ]

	for udocID in udocIDs:

		sents = { x['usentID']:x['sent_length'] for x in list( co_sents.find( {'udocID': udocID} ) ) }
		usentID_offset = min(sents)
		total_words = sum([sents[x] for x in sents])

		th1 = total_words * 0.2
		th2 = total_words * 0.8

		pats = list( co_pats.find( {'udocID': udocID} ) )
		
		for pat in pats:
			
			lanchorID = sum([sents[usentID_offset+i] for i in range(pat['usentID'] - usentID_offset)]) + pat['anchor_idx']
			if lanchorID <= th1: position = 'beginning'
			elif lanchorID <= th2: position = 'middle'
			else: position = 'end'

			key = '#' +  pat['pattern'].lower() + '@' + position
			PatTC[udocID][key] += 1

	# co_dest = db['lexicon.pattern_position_total_count']
	for udocID in PatTC:
		mdoc = { 'udocID': udocID, 'pats': PatTC[udocID].items() }
		co_dest.insert(mdoc)
	co_dest.create_index('udocID')


def create_lexicon_keyword_total_count(co_docs, co_sents, co_keywords, co_cate, wordType='extend', lemma=True):

	from nltk.stem.wordnet import WordNetLemmatizer
	KwTC = defaultdict(Counter)

	# co_docs = db['docs']
	# co_sents = db['sents']
	# co_keywords = db['resource.WordNetAffect']
	# co_cate = db['emotions']

	lmtzr = WordNetLemmatizer()
	emotions = sorted([x['emotion'] for x in co_cate.find({'label':'LJ40K'}, {'_id':0, 'emotion':1})])
	keyword_list = set( [ x['word'].lower() for x in list( co_keywords.find({ 'type': wordType }) ) ] )

	for sent_mdoc in co_sents.find():
		# extract words, pos tags
		words = map(lambda x:x.lower(), sent_mdoc['sent'].strip().split(' '))
		POSs = [x.split('/')[-1] for x in sent_mdoc['sent_pos'].split(' ')]
		word_pos = zip(words, POSs)
		udocID = sent_mdoc['udocID']
		
		for word, pos in word_pos:

			word = word.lower()

			if lemma:
				if pos.startswith('N'): pos = 'n'
				elif pos.startswith('V'): pos = 'v'
				elif pos.startswith('J'): pos = 'a'
				elif pos.startswith('R'): pos = 'r'
				else: pos = None
				if pos: # only lemmatize certain pos types
					word = lmtzr.lemmatize(word, pos)

			if word in keyword_list:
				KwTC[udocID][word] += 1

	co = db[co_lexicon_keyword_tc_name]
	for udocID in KwTC:
		mdoc = { 'udocID': udocID, 'keywords': KwTC[udocID].items() }
		co.insert( mdoc )
	co.create_index('udocID')

## load Pattern-Total-Count lexicon
## format
##  PTC[33680]
	# {u'elaine i': 4,
	#  u'elaine you': 12,
	#  u'elainei love': 4,
	#  u'i love': 1057,
	#  u'i love love': 326,
	#  u'i love you': 340,
	# ...}
##  PTC[33680]['i love you']
	#  340

# KwTC[0]
# {u'bad': 1,
#  u'below': 1,
#  u'best': 1,
#  u'by': 1,
#  u'cut': 1,
#  'do': 1,
#  u'entry': 1,
#  ...
# }
# KwTC[0]['bad']
# 1

## target: pattern, pattern_position, keyword
## create_lexicon_pattern_position_total_count()
## create_lexicon_keyword_total_count(wordType='extend', lemma=True)


### co: collection pointer, e.g., co = db[lexicon.pattern_total_count]
### target: pattern or keywords
def load():
	co_ptc = db[config.co_lexicon_pattern_tc_name]
	TC = {}
	pkl_path = 'cache/' + co_ptc.name + '.pkl'

	if not os.path.exists(pkl_path):

		if co_ptc.find().count() == 0:
			if config.verbose: logging.debug('creating lexicon pattern total count')
			co_dest = create_lexicon_pattern_total_count()
			

		if config.verbose: logging.debug('collecting pattern total count')
		for mdoc in co_ptc.find():
			TC[mdoc['udocID']] = {token: count for token, count in mdoc[target_name]}
		if not os.path.exists('cache'): os.mkdir('cache')
		pickle.dump(TC, open(pkl_path,'wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		TC = pickle.load(open(pkl_path,'rb'))
	return TC	

if __name__ == '__main__':

	create_lexicon_pattern_position_total_count()


