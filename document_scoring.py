import pymongo

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co_docs = db['docs']
co_pats = db['pats']
co_lexicon = db['lexicon']
co_patscore = db['patscore']

## udocID=1000, emotion='happy'
## ds_function=1, opt={'scoring': 1, 'smoothing': 0}, sig_function=0, epsilon=0.5
def document_scoring(udocID, emotion, ds_function, opt, sig_function, epsilon=0.5):

	mDocs = list( co_pats.find( {'udocID': udocID} ) ) 
	# arithmetic mean
	if ds_function == 1:
		docscore = sum( [event_scoring(pat, emotion, opt, sig_function) for pat in mDocs] ) / len(mDocs)
	# geometric mean
	elif ds_function == 2:
		docscore = reduce(lambda x,y:x*y, [event_scoring(pat, emotion, opt, sig_function) for pat in mDocs] )**(1/float(len(a)))
	## undefined ds_function
	else:
		return False
	
	return 1 if docscore >= epsilon else 0

def event_scoring(pat, emotion, opt, sig_function):

	# build query
	query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
	query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0
	
	# fetch pattern score from mongo collection "patscore"
	res = co_patscore.find_one( query )
	prob_p_e = 0.0 if not res else res['prob']
	
	return pat['weight'] * significance_factor(pat, sig_function) * prob_p_e


def significance_factor(pat, sig_function):
	if sig_function == 0: return 1
	if sig_function == 1: return pat['pattern_length']
	if sig_function == 2: return float(1)/pat['sent_length']
	if sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )


if __name__ == '__main__':

	udocID = 1000
	emotion = 'happy'
	ds_function = 1
	opt={'scoring': 1, 'smoothing': 0}
	sig_function = 0
	epsilon = 0.5

	print udocID, emotion, '-->', document_scoring(udocID, emotion, ds_function, opt, sig_function, epsilon)
