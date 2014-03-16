# -*- coding: utf-8 -*-

def significance_factor(pat, function=0):
	if function == 0: return 1
	if function == 1: return pat['pattern_length']
	if function == 2: return float(1)/pat['sent_length']
	if function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )

def event_scoring(pat, emotion, opt):

	# build query
	query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
	query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0

	# fetch pattern score from mongo collection "patscore"
	res = patscore.find_one( query )
	prob_p_e = 0.0 if not res else res['prob']

	return pat['weight'] * sigFactor(pat, function) * prob_p_e