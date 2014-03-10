# -*- coding: utf-8 -*-

### extract pattern according to differernt structure
import sys, os
sys.path.append('/'.join([os.environ['PROJECT_HOME'],'pymodules']))

import color
from ListCombination import ListCombination

from collections import defaultdict
from pprint import pprint

import pymongo, pickle
mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co = db['deps']

# input a list of dep of a document
# output seperated lists containing each sentence
def extract_sents(doc):
	S = defaultdict(list)
	for x in doc: S[x['usentID']].append(x)
	return S.values()

def negation(sent):
	negs = [x for x in sent if x['rel'] == 'neg'] # found negation
	if not negs: return sent
	for neg in negs:
		negtarget = (neg['x'], neg['xIdx'])
		for i, dep in enumerate(sent):
			if (dep['x'], dep['xIdx']) == negtarget: sent[i]['x'] = '_'+sent[i]['x']
			if (dep['y'], dep['yIdx']) == negtarget: sent[i]['y'] = '_'+sent[i]['y']
	return sent

## input all deps of sents
## output set of anchors containing related deps
# {
# 	'VB':
# 	{
# 		('love', 'VBP', 8, 13):
# 		[
# 			{ 'docID': 0, 'emotion': 'accomplished', 'x': 'makes', ...},
# 			{ 'docID': 0, 'emotion': 'accomplished', 'x': 'loopy', ...},
# 		],
#		('took', 'VBD', 3, 13): [ ... ]
# 	},
# 	'JJ': { anchor1: [ dep1, dep2,... ], anchor2: [depi, depj], ... }
# }
def extract_anchors(sent, targets=['VB']):
	D = defaultdict(lambda: defaultdict(list))
	for dep in sent:
		for xy in ['x', 'y']:
			for pos in [t for t in targets if t.lower() in dep[xy+'Pos'].lower()]:
				# anchor (word, pos, wordIndex, usentID)
				anchor = (dep[xy], dep[xy+'Pos'], dep[xy+'Idx'], dep['usentID'])
				if dep not in D[pos][anchor]:
					D[pos][anchor].append(dep)
	return D

##
## D = 
##     {
##  	 'obj' : [ dep1, dep2, ... ],
##     }
## get as long as possible
## 
## sent: i/subj loved/verb you/obj very much
## rule: [(s, 0), (o, 0)]
## ---> 	i loved you
## -x->		loved, i loved, loved you
def apply_rule(deps, rule):

	D = defaultdict(list)
	for dep in deps:
		print '='*30
		print 'current dep', dep
		for rel, mincnt in rule:
			print '\ttest',rel, mincnt,
			if rel == 'prep' and ('prep' in dep['rel']) and ('_' in dep['rel']): # prepc_without, prep_with
				print '\tmatch 1'
				D[dep['rel']].append( dep )
			elif rel in dep['rel']:
				print '\tmatch 2'
				D[rel].append( dep )
			else:
				print '\tcontinue'
				continue

	## check if match the given rule
	for rel, mincnt in rule:
		if len([x for x in D.keys() if rel in x]) < mincnt:
			return False
	return dict(D)

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



def extract_pattern(sent, targets):

	pats = []
	sent = negation(sent)
	anchors = extract_anchors(sent, targets)

	for pos in anchors:

		for anchor_node in anchors[pos]:

			deps = anchors[pos][anchor_node]

			rels = apply_rule(deps, rule)
			if not rels: continue

			combs = ListCombination(rels.values())
			for comb in combs:
				pat = form(comb, anchor_node)
				weight = 1/float(len(combs))
				pats.append((pat,weight))

	return pats

def list_possible_rules(rule):
	## [(s, 0), (o, 0)]
	## --> 		v
	##		s + v
	##			v + o
	##		s + v + o

	## [(s, 1), (o, 0)]
	## --> 	s + v
	##		s + v + o

	## [(s, 1), (o, 1)]
	## --> 	s + v + o
	pass	

if __name__ == '__main__':
	
	udocID = 0
	rule = [('prep', 0), ('subj',0), ('obj',0), ('cop', 0)]
	targets = ['VB', 'JJ']

	for udocID in range(10):

		doc = list(co.find({'udocID':udocID}, {'_id':0}))
		sents = extract_sents(doc)

		for sent in sents:
			pats = extract_pattern(sent, targets)

			sent_str = ' '.join([k[0] for k in sorted(set(reduce(lambda x,y:x+y, [((d['x'],d['xIdx']), (d['y'],d['yIdx'])) for d in sent])), key=lambda a:a[1])])
			print '> %s (%s)' % (sent_str, color.render( str(len(pats)), 'lc'))
			for pat,weight in pats:
				pat_str = ' '.join([x[0] for x in pat])
				print '  '+color.render(pat_str.lower(), 'g'), round(weight,2)

		print '%s end of document %d %s' % ('='*20,udocID, '='*20)
		raw_input()


