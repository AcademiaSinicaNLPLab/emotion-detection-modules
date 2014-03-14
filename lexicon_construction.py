import pymongo
from collections import Counter, defaultdict

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
pats = mc['LJ40K']['pats']
lexicon = mc['LJ40K']['lexicon']

# patCnt: num of patterns in each emotion
# sentlenCnt: sum of sentence length in each emotion
patCnt, sentlenCnt = defaultdict(Counter), defaultdict(Counter)

### cal_pattern_occurrence
## input:  mongo data
## output: { 'pattern': Counter({'emotion': 1, ...}), ... }
def cal_pattern_occurrence():
	for mdoc in pats.find():
		patCnt[mdoc['pattern']][mdoc['emotion']] += 1
		sentlenCnt[mdoc['pattern']][mdoc['emotion']] += mdoc['sent_length']

### construct_lexicon
## input: <dict> patCnt, <dict> sentlenCnt
## output: inject to mongo directly
def construct_lexicon():
	for pattern in patCnt:
		for emotion in patCnt[pattern]:
			avg_sent_len = sentlenCnt[pattern][emotion] / float( patCnt[pattern][emotion] )
			lexicon.insert( {'emotion': emotion, 'pattern': pattern, 'avg_sent_len': avg_sent_len} )

if __name__ == '__main__':
	cal_pattern_occurrence()
	construct_lexicon()