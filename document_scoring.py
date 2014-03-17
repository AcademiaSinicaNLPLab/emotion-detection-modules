import pymongo

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']	
co_docs = db['docs']	
co_pats = db['pats']		
co_lexicon = db['lexicon']
co_patscore = db['patscore']

## udocID=1000, emotion='happy'
## epsilon=0.5, ds_function=1, opt={'scoring': 1, 'smoothing': 0}, sig_function=0
def document_scoring(udocID, emotion, epsilon, ds_function, opt, sig_function): 
	mDocs = list( co_pats.find( {'udocID': udocID} ) ) 
	# arithmetic mean
	if ds_function == 1:
		docscore = sum( event_scoring(pat, emotion, opt, sig_function) for pat in mDocs ) / len(mDocs)
		return 1 if docscore >= epsilon else 0
	# geometric mean
	if ds_function == 2:


def event_scoring(pat, emotion, opt, sig_function):
	# build query
	query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
	query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0
	
	# fetch pattern score from mongo collection "patscore"
	res = co_patscore.find_one( query )
	prob_p_e = 0.0 if not res else res['prob']
	
	return pat['weight'] * sigFactor(pat, sig_function) * prob_p_e


def significance_factor(pat, sig_function):
	if sig_function == 0: return 1
	if sig_function == 1: return pat['pattern_length']
	if sig_function == 2: return float(1)/pat['sent_length']
	if sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )