# -*- coding: utf-8 -*-
import config
import sys, pymongo

from mathutil import standard_deviation as std
from mathutil import avg, normalize, entropy

db = pymongo.Connection(config.mongo_addr)['LJ40K']

# co_patscore = db[ config.co_patscore_names[config.ps_function_type] ]

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
def scoring(pattern_dist, emotion):

	p = pattern_dist[emotion]
	p_bar = [pattern_dist[x] for x in pattern_dist if x != emotion]

	# print emotion, p, p_bar

	np_bar = normalize(p_bar)

	if config.ps_function_type == 0:
		omega_p = (p, sum(p_bar)/float(len(p_bar)) )
		prob_p_e = omega_p[0]/float(sum(omega_p))

	# elif config.ps_function_type == 1:
	# 	delta_p_bar = std(np_bar)
	# 	omega_p = (p, sum(p_bar)/float(len(p_bar))*delta_p_bar )
	# 	prob_p_e = omega_p[0]/float(sum(omega_p))

	elif config.ps_function_type == 1:
		p_score = p
		p_bar_score = std(np_bar)*( max(p_bar)-avg(p_bar) ) / 0.158 + avg(p_bar)
		prob_p_e = p_score/float(p_score+p_bar_score)

	return prob_p_e
#### ------------------- end scoring functions ------------------- ####

## input:  pattern, emotion, function_type
## output: score(pattern, emotion)
def pattern_scoring_function(pattern):

	#### time: 0.00016, exec: (length of all patterns)
	pattern_dist = get_pattern_dist(pattern)

	## score pattern in each emotion
	#### time: 0.00067, exec: (length of all patterns)
	scores = {}
	for emotion in pattern_dist:

		#### scoring time 0.0000167, exec: (length of all patterns) * 40
		score_p_e = scoring(pattern_dist, emotion)

		# print emotion, '\t', score_p_e

		scores[emotion] = score_p_e
	return scores


def update_all_pattern_scores(UPDATE=False, VERBOSE=False):

	cfg = config.toStr(fields="ps_function,smoothing")

	# fetch all distinct patterns
	print >> sys.stderr, 'fetching all distinct patternst...',
	# sys.stderr.flush()

	patterns = set()
	
	for mdoc in co_lexicon.find():
		patterns.add( mdoc['pattern'] )

	# 	if len(patterns) == 1: break 

	#patterns.add('i need girlfriend')
	print >> sys.stderr, 'done'

	

	# calculate pattern scores
	for i,pattern in enumerate(patterns):

		if config.verbose and i % 100 == 0:
			print >> sys.stderr, i,'/',len(patterns)

		# get a set of prob of pattern in each emotion
		#### time: 0.00168, exec: len(patterns);  5.057 when len(patterns) == 3000
		scores = pattern_scoring_function(pattern)

		# insert  Total: 1.00297856331    Loop: 40000     Each: 2.50744640827e-05
		# update  Total: 0.807085752487   Loop: 40000     Each: 2.01771438122e-05
		# save    Total: 1.04345178604    Loop: 40000     Each: 2.6086294651e-05

		## save score to mongo
		#### time: 0.00096, exec, len(patterns);  2.898 when len(patterns) == 3000

		# print >> sys.stderr, '>',pattern
		# print >> sys.stderr, 'emotion'.ljust(13),'|','score'
		# print >> sys.stderr, '------------'.ljust(13),'|','------------'
		# for x in sorted(scores.items(), key=lambda x:x[1], reverse=True)[:5]:
		# 	# print 'hi'.ljust(10)
		# 	# print x[0].ljust(20), round(x[1], 4)
		# 	print >> sys.stderr, x[0].ljust(13), '|', round(x[1], 4)
		# continue

		mdoc = {
			'pattern':pattern,
			'scores':scores
		}

		co_patscore.insert( mdoc )

		# for emotion in scores:

		# 	score = scores[emotion]

			## generate mongo query and upsert
			#### v [update] time: 0.000025, exec, len(patterns)*40;  0.807 when len(patterns) == 1000
			#### x [insert] time: 0.000020, exec, len(patterns)*40;  1.002 when len(patterns) == 1000
			#### x [save]   time: 0.000026, exec, len(patterns)*40;  1.043 when len(patterns) == 1000
			# print i, ')',pattern,'\t', emotion, '(',score,')'
			# continue

			# if UPDATE:
			# 	query = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg }
			# 	update = { '$set': { 'score': score } }
			# 	co_patscore.update( query, update, upsert=True )
			# else:
			# 	mdoc = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg, 'score': score }
			# 	co_patscore.insert( mdoc )

	if config.verbose:
		print >> sys.stderr, 'processed done.'

	print '='*50
	print 'cfg:',cfg

if __name__ == '__main__':

	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hp:s:v',['help','ps_function=', 'smoothing=', 'verbose'])
	except getopt.GetoptError:
		config.help('pattern_scoring', exit=2)

	for opt, arg in opts:
		if opt in ('-h', '--help'): config.help('pattern_scoring')
		elif opt in ('-p','--ps_function'): config.ps_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'): config.smoothing_type = int(arg.strip())
		elif opt in ('-v','--verbose'): config.verbose = True

	## select mongo collections
	co_lexicon = db[config.co_lexicon_name]
	co_patscore = db[ config.co_patscore_names[config.ps_function_type] ]

	print >> sys.stderr, config.ps_function_name, '=', config.ps_function_type
	print >> sys.stderr, config.smoothing_name, '=', config.smoothing_type
	print >> sys.stderr, 'insert collection', '=', config.co_patscore_names[config.ps_function_type]
	print >> sys.stderr, 'verbose =', config.verbose
	print >> sys.stderr, '='*40
	print >> sys.stderr, 'press any key to start...', raw_input()


	import time
	s = time.time()
	update_all_pattern_scores(UPDATE=False)
	print 'Time total:',time.time() - s,'sec'
	



	
