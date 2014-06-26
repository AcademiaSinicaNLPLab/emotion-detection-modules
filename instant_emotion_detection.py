# -*- coding: utf-8 -*-
import sys, os
import pickle, math
import mathutil
import config
import pymongo, color
import json
from collections import defaultdict, Counter
from nltk import Tree
from nltk.stem.wordnet import WordNetLemmatizer
from ListCombination import ListCombination
import jsonrpc

print 'connect mongo'
db = pymongo.Connection(config.mongo_addr)[config.db_name]

print 'init server'
server = jsonrpc.ServerProxy(jsonrpc.JsonRpc20(), jsonrpc.TransportTcpIp(addr=("doraemon.iis.sinica.edu.tw", 12345)))

print 'init WordNetLemmatizer'
lmtzr = WordNetLemmatizer()

abbv = {
	"'m": "am", 
	"'s": {'VBP': "is", 'VBD': 'was', 'default': "is"},
	"'ve": "have",
	"'ll": "will",
	"'re": {'VBP': "are", 'VBD': 'were', 'default': 'are'},
	"'d": {'MD': "would", 'VBD': 'had', 'default': 'would'}
}

targets_rules = {'VB': [('prep', 0), ('subj',0), ('obj',0)],  ## for LJ40K: I have dinner with you
				 'JJ': [('subj',1), ('cop', 1)]}  ## for LJ40K: I am happy


## load pickles
N = pickle.load(open('cache/N.lemma.pkl'))
featID_emotions = pickle.load(open('cache/featID.emotions.pkl'))
featID_N_lemma = pickle.load(open('cache/featID.N.lemma.pkl'))

def restore_abbreviation(abbv, deps):
	for dep in deps:
		for xy in ['x', 'y']:
			w, pos = dep[xy], dep[xy+'Pos']
			if w in abbv:
				if type(abbv[w]) == dict: # ambiguous
					if pos not in abbv[w]:
						dep[xy] = abbv[w]['default']
					else:
						dep[xy] = abbv[w][pos]
				else:
					dep[xy] = abbv[w]
	return deps


def negation(sent, NEG='__'):
	negs = [x for x in sent if x['rel'] == 'neg'] # found negation
	if not negs: 
		return sent
	for neg in negs:
		negtarget = (neg['x'], neg['xIdx'])
		for i, dep in enumerate(sent):
			if (dep['x'], dep['xIdx']) == negtarget: sent[i]['x'] = NEG+sent[i]['x']
			if (dep['y'], dep['yIdx']) == negtarget: sent[i]['y'] = NEG+sent[i]['y']
	return sent


def extract_anchors(sent, targets=['VB']):
	D = defaultdict(lambda: defaultdict(list))
	for dep in sent:
		for xy in ['x', 'y']:
			for pos in [t for t in targets if t.lower() in dep[xy+'Pos'].lower()]:
				# anchor (word, pos, wordIndex, usentID)
				anchor = (dep[xy], dep[xy+'Pos'], dep[xy+'Idx'])
				if dep not in D[pos][anchor]:
					D[pos][anchor].append(dep)
	return D


def apply_rule(deps, rule):

	D = defaultdict(list)
	for dep in deps:
		for rel, mincnt in rule:
			if rel == 'prep' and ('prep' in dep['rel']) and ('_' in dep['rel']): # prepc_without, prep_with
				D[dep['rel']].append( dep )
			elif rel in dep['rel']:
				D[rel].append( dep )
			else:
				continue

	R = {}
	## check if match the given rule
	for rel, mincnt in rule:
		occurrence = len([x for x in D.keys() if rel in x])
		if occurrence < mincnt:
			return False
		R[rel] = occurrence
	return (dict(D), R)


def form(deps, anchor_node):
	words = set()
	for dep in deps:
		words.add( (dep['x'], dep['xPos'], dep['xIdx']) )
		words.add( (dep['y'], dep['yPos'], dep['yIdx']) )

		if 'prep' in dep['rel']:
			prep = '_'.join(dep['rel'].split('_')[1:])
			if not prep: continue

			## predict position
			idx = max(dep['xIdx'], dep['yIdx']) - 1

			words.add((prep, 'IN', idx))
	return sorted(list(words), key=lambda x:x[-1])


## sents format
# sents[0]['parsetree']
# 	'(ROOT (S (VP (NP (INTJ (UH hello)) (NP (NNP Maxis)))) (. .)))'
# sents[0]['dependencies']
# 	[
# 	 ['dep', ['Maxis', 2], ['hello', 1]],
# 	 ['root', ['ROOT', 0], ['Maxis', 2]]
# 	]

## input: <string> doc
## output: pats
def extract_patterns(sents):

	global targets_rules
	global abbv

	pats = []

	for sent in sents:
		
		POSs = Tree( sent['parsetree'] ).pos()
		deps = []
		
		for x in sent['dependencies']:
			if x[0] != 'root':

				dep = {'rel':	x[0], 
					   'x':		x[1][0], 
					   'xIdx':	x[1][1], 
					   'xPos':	POSs[ x[1][1]-1 ][1],
					   'y':		x[2][0], 
					   'yIdx':	x[2][1],
					   'yPos':	POSs[ x[2][1]-1 ][1]}
 
				deps.append(dep)

		deps = negation(deps, NEG='__')
		anchors = extract_anchors( deps, targets_rules.keys() )


		for pos in anchors: ## pos = 'VB' or 'JJ'
			for anchor_node in anchors[pos]:
		
				deps = anchors[pos][anchor_node]
				res = apply_rule( deps, targets_rules[pos] )

				if not res: continue
	
				rels, matched_rule = res
				if not rels: continue

				combs = ListCombination(rels.values())


				for comb in combs:
					comb = restore_abbreviation(abbv, comb)

					pat = form(comb, anchor_node)
					weight = 1/float(len(combs))

					p = {'anchor':anchor_node, 'pat': pat, 'comb':comb, 'weight':weight, 'matched_rule': matched_rule}
					
					pats.append(p)
	return pats


def get_patemo_feat(pats):

	feat = {}
	patscores = Counter()
	
	for pat in pats:
		pattern = ' '.join( [ x[0].lower() for x in pat['pat'] ] )
		mdoc = db['patscore.normal'].find_one({ 'pattern': pattern })
		if mdoc:
			for emo in mdoc['score']:
				patscores[emo] += mdoc['score'][emo]

	for emo in patscores:
		featID = featID_emotions[emo]
		feat[featID] = patscores[emo]

	return feat


def word_counter(sents, lemmatize):

	wc = Counter()

	for sent in sents:
		POSs = Tree( sent['parsetree'] ).pos()
		for t, POS in POSs:
			t = t.lower()
			if lemmatize:
				if POS.startswith('N'): pos = 'n'
				elif POS.startswith('J'): pos = 'a'
				elif POS.startswith('V'): pos = 'v'
				elif POS.startswith('R'): pos = 'r'
				else: pos = None
				if pos:
					t = lmtzr.lemmatize(t, pos)
			wc[t] += 1

	return wc


def get_TF3IDF2_feat(sents, lemmatize):

	feat = {}

	WC = word_counter(sents, lemmatize)

	D = 32000
	delta_d = config.delta_d
	total_words = sum(WC.values())

	max_nt = max(N.values())

	for t in WC:
		idf2 = max_nt - N[t]
		wc = WC[t]
		tf3 = wc / float( wc + total_words/delta_d )
		featID = featID_N_lemma[t]
		feat[featID] = tf3 * idf2

	return feat


## best fusion
# TF3_IDF2 + pat-emo-s-50%
## input: <string> doc
## output: emotion
def instant_emotion_detection(doc, server):


	sents = json.loads( server.parse( doc ) )['sentences']

	## get patterns
	pats = extract_patterns(sents)

	## get pattern features
	pattern_feat = get_patemo_feat(pats)
	print pattern_feat

	## get tfidf features
	tf3idf2_feat = get_TF3IDF2_feat(sents, lemmatize=True)
	print tf3idf2_feat


if __name__ == '__main__':

	
	doc = u"Today I went to donate blood, but my blood didn't flow out smoothly through the first needle. Today was a little chilly, so the nurse said that my vessels were contracting and my blood circulation was not good. After applying a hot compress for a while, they tried again. Actually, I am afraid of needles, even though it is just like getting bitten by a mosquito. I turned my head to distract my attention from the syringe, but the fear of being penetrated inevitably got me nervous. Despite not my first time, it still got me unnerved."
	instant_emotion_detection(doc, server)
