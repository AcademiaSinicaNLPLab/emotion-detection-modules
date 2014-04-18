# -*- coding: utf-8 -*-
import config
import sys, pymongo

from mathutil import standard_deviation as std
from mathutil import avg, normalize, entropy

db = pymongo.Connection(config.mongo_addr)[config.db_name]

# get all emotinos in LJ40K
emotions = sorted([x['emotion'] for x in db[config.co_emotions_name].find({'label':'LJ40K'}, {'_id':0, 'emotion':1})])

### get_pattern_dist
## input: 'i am pissed'
## output: { 'happy': 1, 'crazy': 3, 'pissed off': 25, ...}
## option:
## 		config.smoothing_type: 0 --> no smoothing
##		config.smoothing_type: 1 --> +1
def get_pattern_dist(pattern):
	
	if config.smoothing_type == 0: 
		pdist = dict(zip(emotions, [0]*len(emotions)))

	elif config.smoothing_type == 1: 
		pdist = dict(zip(emotions, [1]*len(emotions)))

	for mdoc in co_lexicon.find( { 'pattern': pattern } ):
		pdist[mdoc['emotion']] += mdoc['count']

	return pdist

#### ------------------- begin scoring functions ------------------- ####
## input:  { emotion: count, ... }
## output: score(pattern, emotion)
## option: 
##	 config.ps_function_type 0: only consider occurrence portion (no distribution information)
##	 config.ps_function_type 1: occurrence + distribution [2014.03.18. discuss with Dr. Ku]
def scoring(pattern_dist, emotion, smoothing=0):


	p = pattern_dist[emotion]
	p_bar = [pattern_dist[x] for x in pattern_dist if x != emotion]

	if smoothing == 1:
		p += 0.25
		p_bar = [x+0.25 for x in p_bar]

	np_bar = normalize(p_bar)

	if config.ps_function_type == 0:
		omega_p = (p, sum(p_bar)/float(len(p_bar)) )
		prob_p_e = omega_p[0]/float(sum(omega_p))

	elif config.ps_function_type == 1:
		p_score = p
		p_bar_score = std(np_bar)*( max(p_bar)-avg(p_bar) ) / 0.158 + avg(p_bar)
		prob_p_e = p_score/float(p_score+p_bar_score)

	elif config.ps_function_type == 2:
		p_score = p
		
		p_bar_score = 0 if sum(p_bar)==0 else sum( [ i*i/float(sum(p_bar)) for i in p_bar ] )
		prob_p_e = p_score/float(p_score + p_bar_score)

	return prob_p_e
#### ------------------- end scoring functions ------------------- ####

## input:  pattern, emotion, function_type
## output: score(pattern, emotion)
def pattern_scoring_function(pattern):

	pattern_dist = get_pattern_dist(pattern)

	if sum(pattern_dist.values()) <= config.droplte:
		return False

	## score pattern in each emotion
	scores = {}
	for emotion in pattern_dist:
		score_p_e = scoring(pattern_dist, emotion)

		scores[emotion] = score_p_e
	return scores


def update_all_pattern_scores(UPDATE=False, VERBOSE=False):

	# fetch all distinct patterns
	print >> sys.stderr, 'fetching all distinct patternst...',
	sys.stderr.flush()

	patterns = set()
	
	for mdoc in co_lexicon.find():
		patterns.add( mdoc['pattern'] )

	print >> sys.stderr, 'done'

	# calculate pattern scores
	for i, pattern in enumerate(patterns):

		if config.verbose and i % 100 == 0:
			print >> sys.stderr, i,'/',len(patterns)

		# get a set of prob of pattern in each emotion
		scores = pattern_scoring_function(pattern)

		if not scores:
			continue

		mdoc = {
			'pattern':pattern,
			'scores':scores
		}

		co_patscore.insert( mdoc )

	if config.verbose:
		print >> sys.stderr, 'processed done.'

if __name__ == '__main__':

	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:s:v',['help','ps_function=', 'smoothing=', 'verbose'])
	except getopt.GetoptError:
		config.help(config.ps_name, exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help(config.ps_name)
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## select mongo collections
	co_lexicon = db[config.co_lexicon_name]

	# get opts of ps_function, smoothing
	# config.co_patscore_name = '_'.join([config.co_patscore_prefix] + config.getOpts(fields="p,s"))
	config.co_patscore_name = '_'.join([config.co_patscore_prefix] + config.getOpts(fields=config.opt_fields[config.ps_name], full=False))
	co_patscore = db[ config.co_patscore_name ]

	print >> sys.stderr, config.ps_function_name, ':', config.ps_function_type
	print >> sys.stderr, config.smoothing_name, ':', config.smoothing_type
	print >> sys.stderr, 'insert collection', ':', config.co_patscore_name
	print >> sys.stderr, 'verbose', ':', config.verbose
	print >> sys.stderr, '='*40
	print >> sys.stderr, 'press any key to start...', raw_input()


	import time
	s = time.time()
	update_all_pattern_scores(UPDATE=False)
	print 'Time total:',time.time() - s,'sec'
	



	
