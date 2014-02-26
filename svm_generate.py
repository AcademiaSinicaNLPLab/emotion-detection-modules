# -*- coding: utf-8 -*-

import pickle, json
from collections import defaultdict, Counter
import util
import pymongo
import nltk

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')

cotf = mc['LJ40K']['tf']
cod = mc['LJ40K']['deps']
cot = mc['LJ40K']['tfidf']

wordlst_path = 'data/'

### options
word_lst_type = None
TF_TYPE = 'TF-0'
IDF_TYPE = 'IDF-1'

if word_lst_type == 'wn': word_lst = set(json.load(open(wordlst_path+'WordNetAffectKeywords.json')))
if word_lst_type == 'ext': word_lst = set(json.load(open(wordlst_path+'WordNetAffectKeywordsExt.json')))
if word_lst_type == None: word_lst = None

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

