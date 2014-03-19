# -*- coding: utf-8 -*-
import config
import sys, pymongo
from mathutil import standard_deviation as std
from mathutil import entropy as ent

db = pymongo.Connection(config.mongo_addr)['LJ40K']

co_lexicon = db[config.co_lexicon_name]
co_patscore = db[config.co_patscore_name]

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
##	 config.ps_function_type 1: consider distribution information by multiplying delta of p_bar
def scoring(pattern_dist, emotion):

	p = pattern_dist[emotion]
	p_bar = [pattern_dist[x] for x in pattern_dist if x != emotion]

	## all zero
	if sum(p_bar) > 0:
		np_bar = [x/float(sum(p_bar)) for x in p_bar]
	else:
		np_bar = p_bar

	if config.ps_function_type == 0:
		omega_p = (p, sum(p_bar)/float(len(p_bar)) )
		prob_p_e = omega_p[0]/float(sum(omega_p))

	elif config.ps_function_type == 1:
		delta_p_bar = std(np_bar)
		omega_p = (p, sum(p_bar)/float(len(p_bar))*delta_p_bar )
		prob_p_e = omega_p[0]/float(sum(omega_p))

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

		scores[emotion] = score_p_e
	return scores


def update_all_pattern_scores(DEBUG=False):

	cfg = config.toStr(fields="ps_function,smoothing")

	# fetch all distinct patterns
	print >> sys.stderr, 'fetching all distinct patternst...',
	sys.stderr.flush()

	patterns = set()
	for mdoc in co_lexicon.find():
		patterns.add( mdoc['pattern'] )
	print >> sys.stderr, 'done'

	# calculate pattern scores
	for i,pattern in enumerate(patterns):

		if DEBUG:
			print i,'/',len(patterns),' --> ',pattern

		# get a set of prob of pattern in each emotion
		#### time: 0.00168, exec: len(patterns);  5.057 when len(patterns) == 3000
		scores = pattern_scoring_function(pattern)

		# insert  Total: 1.00297856331    Loop: 40000     Each: 2.50744640827e-05
		# update  Total: 0.807085752487   Loop: 40000     Each: 2.01771438122e-05
		# save    Total: 1.04345178604    Loop: 40000     Each: 2.6086294651e-05

		## save score to mongo
		#### time: 0.00096, exec, len(patterns);  2.898 when len(patterns) == 3000
		for emotion in scores:

			score = scores[emotion]

			## generate mongo query and upsert
			#### v [update] time: 0.000025, exec, len(patterns)*40;  0.807 when len(patterns) == 1000
			#### x [insert] time: 0.000020, exec, len(patterns)*40;  1.002 when len(patterns) == 1000
			#### x [save]   time: 0.000026, exec, len(patterns)*40;  1.043 when len(patterns) == 1000
			query = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg }
			update = { '$set': { 'score': score } }
			co_patscore.update( query, update, upsert=True )

def _show_help(exit=1):
	print 
	print 'usage: pattern_scoring.py -f <scoring function> -s <smoothing method>'
	print 
	print '  -s, --smoothing: smoothing method'
	print '                   0: no smoothig'
	print '                   1: naive smoothing (+1)'
	print '  -f, --ps_function: scoring function'
	print '                   0: no distribution information, only consider occurrence portion'
	print '                   1: consider distribution information by multiplying the standard deviation (delta of p_bar)'
	if exit: sys.exit(exit)

if __name__ == '__main__':

	import getopt
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hf:s:d',['help','ps_function=', 'smoothing=', 'debug'])
	except getopt.GetoptError:
		_show_help(exit=2)


	debug = False
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			_show_help()
			sys.exit()
		elif opt in ('-f','--function'):
			config.ps_function_type = int(arg.strip())
		elif opt in ('-s','--smoothing'):
			config.smoothing_type = int(arg.strip())
		elif opt in ('-d','--debug'):
			debug = True

	print config.ps_function_name, '=', config.ps_function_type
	print config.smoothing_name, '=', config.smoothing_type
	print 'debug mode:', debug
	print '='*40
	print 'press any key to start...', raw_input()

	update_all_pattern_scores(DEBUG=debug)



	
