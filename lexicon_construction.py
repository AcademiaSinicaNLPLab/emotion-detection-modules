import pymongo
from collections import Counter, defaultdict

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
pats = mc['LJ40K']['pats']
lexicon = mc['LJ40K']['lexicon']

# patCnt: num of patterns in each emotion
patCnt = defaultdict(Counter)

### cal_pattern_occurrence
## input:  mongo data
## output: { 'pattern': Counter({'emotion': 1, ...}), ... }
def cal_pattern_occurrence():
	for mdoc in pats.find():
		patCnt[mdoc['pattern'].lower()][mdoc['emotion']] += 1

### construct_lexicon
## input: <dict> patCnt
## output: inject to mongo directly
def construct_lexicon():
	for pattern in patCnt:
		for emotion in patCnt[pattern]:
			lexicon.insert( {'emotion': emotion, 'pattern': pattern, 'count': patCnt[pattern][emotion] } )

if __name__ == '__main__':
	cal_pattern_occurrence()
	construct_lexicon()
