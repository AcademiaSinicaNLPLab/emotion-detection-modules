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

T = defaultdict(list)

def update_all_pattern_scores(UPDATE=False, DEBUG=False):

	cfg = config.toStr(fields="ps_function,smoothing")

	# fetch all distinct patterns
	print >> sys.stderr, 'fetching all distinct patternst...',
	sys.stderr.flush()

	patterns = set()
	for mdoc in co_lexicon.find():
		patterns.add( mdoc['pattern'] )
		if len(patterns) > 200:
			break
	print >> sys.stderr, 'done'

	# calculate pattern scores
	for i,pattern in enumerate(patterns):

		if i == 200:
			break

		print i,'/',len(patterns),' --> ',pattern


		# get a set of prob of pattern in each emotion
		scores = pattern_scoring_function(pattern)

		
		s = time.time()
		# update mongo
		for emotion in scores:
			score = scores[emotion]


			# upsert to mongo if UPDATE is True
			if i < 100:
				su = time.time()

				## generate mongo query and update
				query = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg }
				update = { '$set': { 'score': score } }
				co_patscore.update( query, update, upsert=True )

				T['update'].append( time.time() - su )

			# directly insert
			else:
				si = time.time()

				mdoc = { 'emotion': emotion, 'pattern': pattern, 'cfg': cfg, 'score': score }
				co_patscore.insert( mdoc )

				T['insert'].append( time.time() - si )

		T['all-scores'].append( time.time() - s )

			
		# if DEBUG:
		# 	print 'processed', pattern

	for key in T:
		print key, '\tTotal:',sum(T[key]), '\tLoop:',len(T[key]), '\tEach:', sum(T[key])/float(len(T[key]))

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

	update_all_pattern_scores(UPDATE=False, DEBUG=debug )



	
