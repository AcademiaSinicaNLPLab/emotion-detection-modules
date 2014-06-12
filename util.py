import sys
sys.path.append('pymodules')

import color
import pickle, os
import logging

## parse raw dependency text
## input
# raw_deps:
# 	poss(dog-2, My-1)
# 	nsubj(likes-4, dog-2)
# 	advmod(likes-4, also-3)
# 	root(ROOT-0, likes-4)
# 	xcomp(likes-4, eating-5)
# 	dobj(eating-5, sausage-6)
## output
# list:	
		# [
		# 	('poss', ('dog', 2), ('My', 1) ),
		# 	...
		# ]
# dict:	
		# [
		# 	{
		# 		'rel': 'poss',
		# 		'ltoken': 'dog',
		# 		'lidx': 2,
		# 		'rtoken': 'My',
		# 		'ridx': 1
		# 	},
		# 	...
		# ]
def read_deps(raw_deps, delimiter=None, auto_detect=False, return_type=list):
	deps = []
	if not delimiter or auto_detect:
		delimiter = '\n' if raw_deps.count('\n') > raw_deps.count('), ') else '), '
	for dep in map(lambda x:x.strip(), raw_deps.strip().split(delimiter)):
		if ')' not in dep.split('-')[-1]: # put ")" back
			dep = dep + ')'
		lpb = [i for (i,x) in enumerate(dep) if x == '(']
		rpb = [i for (i,x) in enumerate(dep) if x == ')']
		if not lpb or not rpb: continue

		dl = min(lpb)
		dr = max(rpb)

		rel = dep[:dl]
		body = dep[dl+1:dr]

		parts = body.split(', ')

		left, right = map(lambda x: ( '-'.join(x.split('-')[:-1]), int( x.split('-')[-1].replace("'",'') ) ), parts)

		if return_type == dict:
			deps.append( {'rel':rel, 'ltoken': left[0], 'lidx': left[1], 'rtoken': right[0], 'ridx': right[1]} )
		else:
			deps.append((rel , left, right))
	return deps

## input
# raw_wordpos
# 	My/PRP$ dog/NN also/RB likes/VBZ eating/VBG sausage/NN ./.
#
## output
# 	[(My,PRP$), (dog/NN), ...]
def read_words(raw_wordpos, delimiter=' '):
	return [('/'.join(word_pos_str.split('/')[:-1]), word_pos_str.split('/')[-1]) for word_pos_str in raw_wordpos.strip().split(delimiter)]

### check index
# input: list of ( collection pointer, index name ) tuple
# check_list = [
# 	(co_docs, config.category), ## 
# 	(co_pats, 'udocID')
# ]
def check_indexes(check_list, verbose=True):
	res = []
	for co, idx_name in check_list:
		INDEXED = False
		current_idx_full_names = co.index_information().keys()
		for current_idx_full_name in current_idx_full_names:
			current_idx = '_'.join(current_idx_full_name.split('_')[:-1]) 
			if current_idx == idx_name:
				INDEXED = True
				break
		if verbose: logging.info('collection: %s, index: %s (%s)' % (color.render(co.full_name, 'y'), color.render(idx_name,'g'), 'o' if INDEXED else 'x') )
		if not INDEXED:
			co.create_index(idx_name)
			if verbose: logging.warn('create index on %s in %s' % (color.render(idx_name, 'g'), color.render(co.full_name, 'y') ))

def pattern_scoring_function(pat_counts):

	score = {}
	for anchor in pat_counts:

		SUM = float( sum( [ pat_counts[category] for category in pat_counts if category != anchor ] ) )
		SUMSQ = float( sum( [ (pat_counts[category] ** 2) for category in pat_counts if category != anchor ] ) )
		
		anchor_value = float( pat_counts[anchor] )
		not_anchor_value = float( SUMSQ/( SUM + 0.9 ** SUM ) )
		
		score[anchor] = anchor_value / (anchor_value + not_anchor_value)

	return score


## load entire mongo.LJ40K.docs into memory
def load_mongo_docs(co_docs):
	mongo_docs = {}
	if not os.path.exists('cache/'+co_docs.full_name+'.pkl'):
		if not os.path.exists('cache'): os.mkdir('cache')
		for mdoc in co_docs.find({}, {'_id':0}):
			udocID = mdoc['udocID']
			del mdoc['udocID']
			mongo_docs[udocID] = mdoc
		pickle.dump(mongo_docs, open('cache/'+co_docs.full_name+'.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		mongo_docs = pickle.load(open('cache/'+co_docs.full_name+'.pkl','rb'))
	return mongo_docs

##  PTC[33680]['i love you']
##  340 
def load_lexicon_pattern_total_count(co_ptc, lexicon_type='lexicon'):
	PatTC = {}
	# co_ptc = db['lexicon.pattern_total_count']
	pkl_path = 'cache/PTC.'+lexicon_type+'.pkl'
	if not os.path.exists(pkl_path):
		for mdoc in co_ptc.find():
			PatTC[mdoc['udocID']] = {pat: count for pat, count in mdoc['pats']}
		if not os.path.exists('cache'): os.mkdir('cache')
		pickle.dump(PatTC, open(pkl_path,'wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		PatTC = pickle.load(open(pkl_path,'rb'))
	return PatTC


## KwTC[0]['bad']
## 1
def load_lexicon_keyword_total_count(co_ktc):
	KwTC = {}
	# co_ktc = db['lexicon.keyword_total_count']
	if not os.path.exists('cache/KwTC.lexicon.pkl'):
		for mdoc in co_ktc.find():
			KwTC[mdoc['udocID']] = {kw: count for kw, count in mdoc['keywords']}
		if not os.path.exists('cache'): os.mkdir('cache')
		pickle.dump(KwTC, open('cache/KwTC.lexicon.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	else:
		KwTC = pickle.load(open('cache/KwTC.lexicon.pkl','rb'))
	return KwTC



