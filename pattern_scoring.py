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
## 		smoothing_method: 0 --> no smoothing
##		smoothing_method: 1 --> +1
def get_pattern_dist(pattern, smoothing_method):
	
	if smoothing_method == 0: 
		pdist = dict(zip(emotions, [0]*len(emotions)))

	elif smoothing_method == 1: 
		pdist = dict(zip(emotions, [1]*len(emotions)))

	for mdoc in co_lexicon.find( { 'pattern': pattern } ):
		pdist[mdoc['emotion']] += mdoc['count']

	return pdist

#### ------------------- scoring functions ------------------- ####

### scoring
## input:  { emotion: count, ... }
## output: score(pattern, emotion)
## option: 
##	 function 0: only consider occurrence portion (no distribution information)
##	 function 1: consider distribution information by multiplying delta of p_bar
def scoring(pattern_dist, emotion, f):
	p = pattern_dist[emotion]
	p_bar = [pattern_dist[x] for x in pattern_dist if x != emotion]
	## all zero
	if sum(p_bar) > 0:
		np_bar = [x/float(sum(p_bar)) for x in p_bar]
	else:
		np_bar = p_bar

	if f == 0:
		omega_p = (p, sum(p_bar)/float(len(p_bar)) )
		prob_p_e = omega_p[0]/float(sum(omega_p))

	elif f == 1:
		delta_p_bar = std(np_bar)
		omega_p = (p, sum(p_bar)/float(len(p_bar))*delta_p_bar )
		prob_p_e = omega_p[0]/float(sum(omega_p))

	return prob_p_e

#### ------------------- scoring functions ------------------- ####

### pattern_scoring_function
## input:  pattern, emotion, function_type
## output: score(pattern, emotion)
def pattern_scoring_function(pattern, function, smoothing_method):
	## smoothing method is for pattern distribution
	pattern_dist = get_pattern_dist(pattern, smoothing_method)

	## score pattern in each emotion
	scores = {}
	for emotion in pattern_dist:
		score_p_e = scoring(pattern_dist, emotion, function)
		scores[emotion] = score_p_e
	return scores

def update_all_pattern_scores(fs_function, smoothing_method, debug=False):

	# fetch all distinct patterns
	patterns = set()
	for mdoc in co_lexicon.find():
		patterns.add( mdoc['pattern'] )

	if debug:
		print >> sys.stderr, 'get all distinct patterns'

	# calculate pattern scores
	for pattern in patterns:

		# get a set of prob of pattern in each emotion
		scores = pattern_scoring_function(pattern, fs_function, smoothing_method)

		# update mongo
		for emotion in scores:
			score = scores[emotion]

			# form query and update doc
			##### old version #####
			# query = { 'emotion': emotion, 'pattern': pattern, 'scoring': fs_function, 'smoothing': smoothing_method }

			##### new version #####

			## generate cfg string
			cfg = { 
					config.ps_function_name: fs_function, 
					config.smoothing_name: smoothing_method 
			}
			cfg = config.transform_cfg(cfg)

			## generate mongo query
			query = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg }
			update = { '$set': { 'score': score } }

			# upsert to mongo
			co_patscore.update( query, update, upsert=True )

			
		if debug:
			print 'processed', pattern

def _show_help(exit=1):
	print 
	print 'usage: pattern_scoring.py -f <scoring function> -s <smoothing method>'
	print 
	print '  -s, --smoothing: smoothing method'
	print '                   0: no smoothig'
	print '                   1: naive smoothing (+1)'
	print '  -f, --function: scoring function'
	print '                   0: no distribution information, only consider occurrence portion'
	print '                   1: consider distribution information by multiplying the standard deviation (delta of p_bar)'
	if exit: sys.exit(exit)

if __name__ == '__main__':

	import getopt
	
	# if len(sys.argv) == 1: _show_help(exit=1)
	
	try:
		opts, args = getopt.getopt(sys.argv[1:],'hf:s:d',['help','function=', 'smoothing=', 'debug'])
	except getopt.GetoptError:
		_show_help(exit=2)


	ps_function = config.ps_function_type
	smoothing =  config.smoothing_type

	debug = False
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			_show_help()
			sys.exit()
		elif opt in ('-f','--function'):
			ps_function = int(arg.strip())
		elif opt in ('-s','--smoothing'):
			smoothing = int(arg.strip())
		elif opt in ('-d','--debug'):
			debug = True

	print 'scoring function:', ps_function
	print 'smoothing method:', smoothing
	print 'debug mode:', debug
	print '...correct?', raw_input()

	update_all_pattern_scores( ps_function, smoothing, debug=debug )



	
