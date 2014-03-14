import pymongo
from collections import Counter, defaultdict

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
pats = mc['LJ40K']['pats']
lexicon = mc['LJ40K']['lexicon']

patCnt, sentCnt = defaultdict(Counter), defaultdict(Counter)

## input:  mongo data
## output: { 'pattern': Counter({'emotion': 1, ...}), ... }
def cal_pattern_occurrence():
	for mdoc in pats.find():
		patCnt[mdoc['pattern']][mdoc['emotion']] += 1
		sentCnt[mdoc['pattern']][mdoc['emotion']] += mdoc['sent_length']

## input: <dict> patCnt, <dict> sentCnt
## output: inject to mongo directly
def construct_lexicon():
	for pattern in patCnt:
		for emotion in patCnt[pattern]:
			avg_sent_len = sentCnt[pattern][emotion] / float( patCnt[pattern][emotion] )
			lexicon.insert( {'emotion': emotion, 'pattern': pattern, 'avg_sent_len': avg_sent_len} )
