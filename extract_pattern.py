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
	for x in doc: S[x['sentID']].append(x)
	return S.values()

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
				anchor = (dep[xy], dep[xy+'Pos'], dep[xy+'Idx'], dep['sentID'])
				if dep not in D[pos][anchor]:
					D[pos][anchor].append(dep)			
	return D

##
##
# {
# 	'obj' : [ dep1, dep2, ... ],
# }
def apply_rule(deps, rule):
	D = defaultdict(list)
	for dep in deps:
		for rel, mincnt in rule:
			if rel == 'prep' and '_' in dep['rel']:
				D[dep['rel']].append( dep )
			elif rel in dep['rel']:
				D[rel].append( dep )
			else:
				continue
	## check if achieve minimum count
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
			# print dep['rel'], '-->', prep
			words.add((prep, 'IN', idx))
			# raw_input()

	return sorted(list(words), key=lambda x:x[-1])

def negation(sent):
	negs = [x for x in sent if x['rel'] == 'neg'] # found negation
	if not negs: return sent
	for neg in negs:
		negtarget = (neg['x'], neg['xIdx'])
		for i, dep in enumerate(sent):
			if (dep['x'], dep['xIdx']) == negtarget: sent[i]['x'] = '_'+sent[i]['x']
			if (dep['y'], dep['yIdx']) == negtarget: sent[i]['y'] = '_'+sent[i]['y']
	return sent

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
				# print len(pat)
				pats.append((pat,weight))

	return pats

if __name__ == '__main__':
	
	udocID = 0
	rule = [('prep', 0), ('subj',0), ('obj',0)]
	targets = ['VB', 'JJ']

	for udocID in range(10):

		doc = list(co.find({'udocID':udocID}))
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


