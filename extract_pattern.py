# -*- coding: utf-8 -*-

## python extract_pattern.py -d NTCIR --topic --verbose

### extract pattern according to differernt structure
import sys, os
# sys.path.append('/'.join([os.environ['PROJECT_HOME'],'pymodules']))

import color
from ListCombination import ListCombination

import config

from collections import defaultdict
from pprint import pprint

import pymongo, pickle
mc = pymongo.Connection(config.mongo_addr)

topic_or_emotion = 'emotion'

# verb_frame = (['VB'], [('prep', 0), ('subj',0), ('obj',0)]) ## for LJ40K: I love you
verb_frame = (['V'],  [('prep', 0), ('subj',0), ('obj',0)]) ## for NTCIR
# be_status = (['JJ'], [('subj',1), ('cop', 1)]) ## for LJ40K: I am happy
be_status = (['VC'],  [('top',1), ('attr', 1)]) ## for NTCIR

# input a list of dep of a document
# output seperated lists containing each sentence
def extract_sents(doc):
	S = defaultdict(list)
	for x in doc:
		S[x['usentID']].append(x)
	return S.values()

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

abbv = {
	"'m": "am", 
	"'s": {'VBP': "is", 'VBD': 'was', 'default': "is"},
	"'ve": "have",
	"'ll": "will",
	"'re": {'VBP': "are", 'VBD': 'were', 'default': 'are'},
	"'d": {'MD': "would", 'VBD': 'had', 'default': 'would'}
}
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



def extract_pattern(sent, targets, rule):

	pats = []
	sent = negation(sent, NEG='__')
	anchors = extract_anchors(sent, targets)

	for pos in anchors:

		for anchor_node in anchors[pos]:

			deps = anchors[pos][anchor_node]

			# print anchor_node


			res = apply_rule(deps, rule)
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

# {
#     pattern: "i _love you",
#     anchor: "love",
#     anchortype: "verb",
#     dID: 1,
#     sID: 2,
#     vidx: 13,
#     negation: True,
#     pLen: 3
#     sLen: 10
#     rule: 
#     {
#         'subject': 1,
#         'object' : 1,
#         'prep'   : 0
#     }
# }
def store_mongo(sent, pats, mongo_collection, topic_or_emotion='emotion'):

	for p in pats:

		doc = {}
		doc['sent_length'] = sent[0]['sent_length']
		doc['udocID'] = sent[0]['udocID']
		doc['usentID'] = sent[0]['usentID']
		doc[topic_or_emotion] = sent[0][topic_or_emotion]		

		doc['pattern_length'] = len(p['pat'])
		doc['pattern'] = ' '.join([x[0] for x in p['pat']])
		doc['rule'] = p['matched_rule']

		doc['anchor'] = p['anchor'][0]
		doc['anchor_type'] = p['anchor'][1]
		doc['anchor_idx'] = p['anchor'][2]

		doc['weight'] = p['weight']
		
		mongo_collection.save(doc)


if __name__ == '__main__':

	import getopt

	add_opts = [
		('--database', ['-d or --database: specify the destination database name']),
		('--topic', ['--topic: identify as "topic" rather than "emotion"']),
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hd:v',['help','database=','topic','verbose'])
	except getopt.GetoptError:
		config.help('extract_pattern', addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('extract_pattern', addon=add_opts)
		elif opt in ('-d','--database'): config.db_name = arg.strip()
		elif opt in ('-v','--verbose'): config.verbose = True
		elif opt in ('--topic'): topic_or_emotion = 'topic'

	db = mc[config.db_name]
	co_deps = db[config.co_deps_name]
	co_pats = db[config.co_pats_name]

	# # rule = [('subj',1), ('cop', 1)]
	# rule = [('prep', 0), ('subj',0), ('obj',0)]
	# # targets = ['JJ']
	# targets = ['VB']

	targets_rules = [verb_frame, be_status]

	udocIDs = co_deps.distinct('udocID')
	# udocIDs = [0]
	MaxudocID = max(udocIDs)

	for targets, rule in targets_rules:
		
		# print 'targets:',targets
		# print 'rule:',rule
		# raw_input()
		for udocID in udocIDs:

			doc = list(co_deps.find( {'udocID':udocID} ))

			## extract all sentences in one document
			sents = extract_sents(doc)

			for sent in sents:

				## for each sentence, extract patterns
				pats = extract_pattern(sent, targets, rule)

				## display results
				if config.verbose:
					sent_str = ' '.join([k[0] for k in sorted(set(reduce(lambda x,y:x+y, [((d['x'],d['xIdx']), (d['y'],d['yIdx'])) for d in sent])), key=lambda a:a[1])][1:] )
					print '> %s (%s)' % (sent_str, color.render( str(len(pats)), 'lc'))
					for p in pats:
						pat_str = ' '.join([x[0] for x in p['pat']])
						print '  '+color.render(pat_str.lower(), 'g'), round(p['weight'],2)

				## store back in mongo
				store_mongo(sent, pats, co_pats, topic_or_emotion)

			print '> %s / %s' % (udocID, MaxudocID )
			if config.verbose:
				print '%s end of document %d %s' % ('='*20,udocID, '='*20)
