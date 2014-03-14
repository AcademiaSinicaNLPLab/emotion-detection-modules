import pymongo
from mathutil import standard_deviation as std
from mathutil import entropy as ent

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
lexicon = mc['LJ40K']['lexicon']

### get_pattern_dist
## input: 'i am pissed'
## output: { 'happy': 1, 'crazy': 3, 'pissed off': 25, ...}
def get_pattern_dist(pattern):
	return dict([(x['emotion'],x['count']) for x in list(lexicon.find( { 'pattern': pattern }))])

### pattern_scoring
## input:  { emotion: count, ... }
## output: score(pattern, emotion)
def pattern_scoring(pattern_dist, emotion):
	p = pattern_dist[emotion]
	p_bar = [pattern_dist[x] for x in pattern_dist if x != emotion]
	np_bar = [x/float(sum(p_bar)) for x in p_bar]
	delta_p_bar = std(np_bar)
	omega_p = (p, sum(p_bar)/float(len(p_bar))*delta_p_bar )
	prob_p_e = omega_p[0]/float(sum(omega_p))
	return prob_p_e

