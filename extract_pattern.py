# -*- coding: utf-8 -*-

## python extract_pattern.py -d NTCIR --topic --verbose

### extract pattern according to differernt structure
import sys
sys.path.append('pymodules')
import config
import logging, json
import pymongo
import os
import pickle
from collections import Counter, defaultdict

import color
from ListCombination import ListCombination

mc = pymongo.Connection(config.mongo_addr)


# verb_frame = (['VB'], [('prep', 0), ('subj',0), ('obj',0)]) ## for LJ40K: I love you
verb_frame = (['V'],  [('prep', 0), ('subj',0), ('obj',0)]) ## for NTCIR
# be_status = (['JJ'], [('subj',1), ('cop', 1)]) ## for LJ40K: I am happy
be_status = (['VC'],  [('top',1), ('attr', 1)]) ## for NTCIR

# # rule = [('subj',1), ('cop', 1)]
# rule = [('prep', 0), ('subj',0), ('obj',0)]
# # targets = ['JJ']
# targets = ['VB']

co_deps = None
co_pats = None

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
def run(targets_rules):

	udocIDs = co_deps.distinct('udocID')

	MaxudocID = max(udocIDs)
	

	for targets, rule in targets_rules:
		
		rule_str = color.render(' '.join([str(x)+','+str(y) for x,y in rule]), 'lightblue')

		for udocID in udocIDs:

			logging.info(' process %d/%d; rule: %s' % (udocID, MaxudocID, rule_str))

			doc = list(co_deps.find( {'udocID':udocID} ))

			## extract all sentences in one document
			sents = extract_sents(doc)

			for sent in sents:

				## extract patterns in each sentence
				pats = extract_pattern(sent, targets, rule)

				## display results
				if config.verbose:
					sent_str = ' '.join([k[0] for k in sorted(set(reduce(lambda x,y:x+y, [((d['x'],d['xIdx']), (d['y'],d['yIdx'])) for d in sent])), key=lambda a:a[1])][1:] )
					logging.debug('%s (%d)' % (sent_str, len(pats)))
					for p in pats:
						pat_str = ' '.join([x[0] for x in p['pat']])
						logging.debug('   %s %.1f' % (color.render(pat_str.lower(), 'g'), p['weight']))

				## store back in mongo
				for p in pats:
					mdoc = {
						'sent_length': 		sent[0]['sent_length'],
						'udocID': 			sent[0]['udocID'],
						'usentID': 			sent[0]['usentID'],
						config.category: 	sent[0][config.category],

						'pattern_length': 	len(p['pat']),
						'pattern': 			' '.join([x[0] for x in p['pat']]),
						'rule': 			p['matched_rule'],

						'anchor': 			p['anchor'][0],
						'anchor_type': 		p['anchor'][1],
						'anchor_idx': 		p['anchor'][2],

						'weight': 			p['weight']
					}
					co_pats.insert(mdoc)

if __name__ == '__main__':

	program = __file__.split('.py')[0]

	import getopt

	add_opts = [
		('--database', ['-d or --database: specify the destination database name']),
	]

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hovd:',['help','overwrite','verbose', 'database='])
	except getopt.GetoptError:
		config.help(program, addon=add_opts, exit=2)

	## read options
	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(program, addon=add_opts)
		elif opt in ('-d','--database'): config.db_name = arg.strip()
		elif opt in ('-o','--overwrite'): config.overwrite = True
		elif opt in ('-v','--verbose'): config.verbose = True

	loglevel = logging.DEBUG if config.verbose else logging.INFO
	logging.basicConfig(format='[%(levelname)s] %(message)s', level=loglevel)


	db = mc[config.db_name]

	## src
	co_deps = db[config.co_deps_name]
	## dest
	co_pats = db[config.co_pats_name]

	### check whether destination collection is empty or not
	dest_cos = [co_pats]
	dest_cos_status = {co.name : co.count() for co in dest_cos}
	logging.info('current collection status: ' + json.dumps(dest_cos_status))
	if sum(dest_cos_status.values()) > 0 and not config.overwrite:
		logging.warn('use --overwrite or -o to drop current data and insert new one')
		exit(-1)
	elif sum(dest_cos_status.values()) > 0 and config.overwrite:
		# logging.warn('overwrite mode, will drop all data in ' + )
		print >> sys.stderr, 'drop all data in',', '.join(dest_cos_status.keys()), '(Y/n)? ', 
		if raw_input().lower().startswith('n'): exit(-1)
		else: 
			for co in dest_cos: co.drop()

	targets_rules = [verb_frame, be_status]

	run(targets_rules)
