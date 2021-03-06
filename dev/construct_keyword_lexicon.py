# -*- coding: utf-8 -*-
import sys
sys.path.append('../')

import config
import pymongo, color
from collections import defaultdict, Counter
from nltk.stem.wordnet import WordNetLemmatizer

db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_docs = db['docs']
co_sents = db['sents']
co_keywords = db['resource.WordNetAffect']

lmtzr = WordNetLemmatizer()

emotions = sorted([x['emotion'] for x in db['emotions'].find({'label':'LJ40K'}, {'_id':0, 'emotion':1})])


# build lexicon storing keyword occurrence
def build_lexicon():

	print 'type: ', wordType
	print 'lemma: ', str(lemma)

	keyword_list = [ x['word'] for x in list( co_keywords.find({ 'type': wordType }) ) ]

	keywordCount = defaultdict(Counter)

	for (ie, e) in enumerate(emotions):

		print >> sys.stderr, '%d > %s' % ( ie, color.render(e, 'g') )

		for doc in co_docs.find( { 'emotion': e, 'ldocID': {'$lt': 800}} ):

			udocID = doc['udocID']
			mdocs = list( co_sents.find( {'udocID': udocID} ) )
			
			for mdoc in mdocs:
			
				words = mdoc['sent'].split(' ')
				POSs = [ x.split('/').pop() for x in mdoc['sent_pos'].split(' ') ]
			
				for idx, word in enumerate(words):
			
					word = word.lower()

					if lemma:
										
						if POSs[idx].startswith('N'): pos = 'n'
						elif POSs[idx].startswith('V'): pos = 'v'
						elif POSs[idx].startswith('J'): pos = 'a'
						elif POSs[idx].startswith('R'): pos = 'r'
						else: pos = None	
						if pos:
							word = lmtzr.lemmatize(word, pos)

					if word in keyword_list:
						keywordCount[word][e] += 1

	for word in keywordCount:
		mdoc = {
			'keyword': word,
			'count': keywordCount[word]
		}
		co_keyword_lexicon.insert( mdoc )


if __name__ == '__main__':

	## usage: python construct_keyword_lexicon.py [basic/extend] [wo_lemma/w_lemma]

	if len(sys.argv) < 3:
		print 'construct all lexicon? [y/N]'
		yn = raw_input().strip()
		if yn.lower() == 'y':

			## setting 1
			wordType = 'basic'
			lemma = False	
			co_keyword_lexicon = db['lexicon.keyword.basic.wo_lemma']
			build_lexicon()

			## setting 2
			wordType = 'basic'
			lemma = True	
			co_keyword_lexicon = db['lexicon.keyword.basic.w_lemma']
			build_lexicon()

			## setting 3
			wordType = 'extend'
			lemma = False	
			co_keyword_lexicon = db['lexicon.keyword.extend.wo_lemma']
			build_lexicon()

			## setting 4
			wordType = 'extend'
			lemma = True	
			co_keyword_lexicon = db['lexicon.keyword.extend.w_lemma']
			build_lexicon()
		else:
			print 'usage: python construct_keyword_lexicon.py [basic/extend] [wo_lemma/w_lemma]'
			exit(0)
	else:
		basic_extend = sys.argv[1].strip()
		wo_lemma_w_lemma = sys.argv[2].strip()

		if not basic_extend in ['basic', 'extend'] or not wo_lemma_w_lemma in ['wo_lemma', 'w_lemma']:
			print 'invalid arguments'
			print 'usage: python construct_keyword_lexicon.py [basic/extend] [wo_lemma/w_lemma]'
			exit(0)

		wordType = basic_extend
		lemma = False if wo_lemma_w_lemma.startswith('wo') else True
		co_keyword_lexicon = db['lexicon.keyword.'+wordType+'.'+wo_lemma_w_lemma]
		build_lexicon()



