
import os, sys, pickle
import pymongo

def fetch_emotions():

	if os.path.exists('../cache/emotions.pkl'):
		E = pickle.load(open('../cache/emotions.pkl', 'rb'))
	else:
		if not os.path.exists('../cache'): os.mkdir('../cache')


		db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['LJ40K']
		LJ40K = map(lambda x:x['emotion'], db['emotions'].find({'label': 'LJ40K'}))
		Mishne05 = map(lambda x:x['emotion'], db['emotions'].find({'label': 'Mishne05'}))
		intersection = [e for e in set(LJ40K+Mishne05) if e in LJ40K and e in Mishne05]

		E = {
			'LJ40K': LJ40K,
			'Mishne05': Mishne05,
			'intersection': intersection
		}
		pickle.dump(E, open('../cache/emotions.pkl','wb'), protocol=pickle.HIGHEST_PROTOCOL)
	return E

def show(exp_name):

	d = eval(open('../results/'+exp_name+'.txt').read().strip())

	emotions = fetch_emotions()

	for e, a in sorted(d.items(), key=lambda x:x[1], reverse=True):
		if e in emotions['intersection']:
			label = 'o'
		elif e in emotions['LJ40K']:
			label = 'x (LJ40K)'
		elif e in emotions['Mishne05']:
			label = 'x (Mishne05)'
		else:
			label = '?'

		print '\t'.join([e, str(a), label])

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print 'python show.py [exp_name]'
		print '\t e.g., python show.py kw-bag+pat-emo-s'
		exit(-1)

	exp_name = sys.argv[1]
	show(exp_name)
