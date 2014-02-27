# -*- coding: utf-8 -*-

import pymongo, json, sys
from pprint import pprint
from collections import Counter

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')

## ------------------------- options -------------------------- ##

corpus = 'LJ40K'
word_lst_type = 'ext'
TF_TYPE = 'TF-0'
IDF_TYPE = 'IDF-1'
METHOD = TF_TYPE+'x'+IDF_TYPE
DISTINCT_WORDS = False
wordlst_path = 'data/'

#!!! must change postfix and part_range at the same time
postfix = 'test'
part_range = [0,800]

ext = 'txt'

## ------------------------------------------------------------ ##

db = mc[corpus]

def init_wid(word_lst): return dict(list([(w,i) for i,w in enumerate(sorted(word_lst))]))
def init_gid(label='LJ40K'): return dict( [ (document['emotion'],i) for i,document in enumerate( sorted( list( db['emotions'].find({'label':label}) ), key=lambda x:x['emotion'] ) ) ] )

## init
if word_lst_type == 'wn': word_lst = init_wid(json.load(open(wordlst_path+'WordNetAffectKeywords.json')))
if word_lst_type == 'ext': word_lst = init_wid(json.load(open(wordlst_path+'WordNetAffectKeywordsExt.json')))
if word_lst_type == None: word_lst = None

emotions = init_gid()

def slice_corpus(co, data_range=[800, -1]):
	data_range.sort()
	if -1 in data_range:
		operators = { '$gte': data_range[1] }
	else:
		operators = { '$gte': data_range[0], '$lt': data_range[1] }
	cur = co.find( {'local_docID': operators }, {'emotion':1, 'docID': 1, '_id': 0})
	return [(document['docID'], document['emotion']) for document in cur]

def deps_to_article(deps, wordlst=None):
	doc = set()
	for dep in deps:
		X = (dep['x'].lower(), dep['xIdx'], dep['sentID'])
		Y = (dep['y'].lower(), dep['yIdx'], dep['sentID'])
		if wordlst:
			if dep['x'].lower() in wordlst: doc.add(X)
			if dep['y'].lower() in wordlst: doc.add(Y)
		else:
			doc.add(X)
			doc.add(Y)
	doc = [x[0] for x in doc]
	return doc


_cache = {}
def vectoring(db, doc, gold, wordlst):

	vector = set()

	# get emotion id
	gid = emotions[gold]

	features = Counter()

	if DISTINCT_WORDS:
		doc = set(doc)

	for w in doc:
		if w not in wordlst:
			continue
		else:
			if w not in _cache:
				fetch = db['tfidf'].find_one( {'word': w, 'emotion':gold, 'tf-type': TF_TYPE, 'idf-type': IDF_TYPE } )
				if not fetch:
					continue
				else:
					_cache[w] = fetch
					
			# get word id
			wid = wordlst[w]

			## ------ change scoring method here ------
			tfidf = _cache[w]['tfidf']
			# tf = _cache[w]['tf']
			score = tfidf
			## --------- end of scoring method --------

			# generate feature, e.g., 1:20
			features[wid] += score

	if len(features) > 0:

		## ensure feature indices are in an ascending order
		vector = sorted( features.items(), key=lambda x:x[0] ) 	# [(1, 100), (2, 50), (5, 90), ...]
		vector = [str(wid)+':'+str(score) for wid,score in vector]

		# set gold class number
		vector.insert(0, str(gid) )
		return ' '.join(vector)
	else:
		return None
	


def generate(db, corpus, wordlst, out):
	with open(out, 'w') as fw:
		for (i, (udocID, gold) ) in enumerate(corpus):
			print '[%d/%d] process %s %d' % (i, len(corpus), gold, udocID)
			# fetch dependency
			deps = list(db['deps'].find( {'udocID': udocID} ))
			# extract words
			doc = deps_to_article(deps)
			# build vector
			line = vectoring(db, doc, gold, wordlst)
			if not line: continue
			fw.write(line + '\n')

if __name__ == '__main__':


	opt = '' if not DISTINCT_WORDS else '-distinct'

	fn = [corpus, METHOD]

	if word_lst_type: fn.append(word_lst_type)

	out_filename = '_'.join(fn)

	if opt:
		out_filename += opt
	out_filename = '.'.join([out_filename, postfix, ext])

	cfg = { 
		'filename': out_filename, 
		'corpus': corpus, 
		'word_lst_type': word_lst_type,
		'method': METHOD,
		'detail': 
		{ 
			'TF_TYPE': TF_TYPE, 
			'IDF_TYPE':IDF_TYPE 
		},
		'opt': 
		{ 
			'distinct': DISTINCT_WORDS 
		},
		'type': postfix,
		'range': part_range,
	}
	pprint(cfg)
	raw_input()

	db['svmcfg'].update( {'filename':out_filename}, { cfg }, upsert=True )

	# if not db['svmcfg'].find_one( { 'filename':out_filename } ):
	# 	db['svmcfg'].insert(cfg)

	# set data range to collect part of entire corpus
	part = slice_corpus(co=mc['LJ40K']['mapping'], data_range=part_range)

	# generate train, test, dev files
	generate(db=mc['LJ40K'], corpus=part, wordlst=word_lst, out='/Users/Maxis/corpus/svm/'+out_filename)
