# -*- coding: utf-8 -*-

import pickle, json
from collections import defaultdict, Counter
import pymongo
import nltk, color
from mathutil import entropy
from mathutil import standard_deviation as SD


mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')

co = mc['LJ40K']['tf']


D = defaultdict(lambda: Counter())
# {
# 	'<emotion> happy':
# 		<Counter>
#		{
#			'<word> good': 1000,
#			'<word> suck': 10, ...
#		}
# }
for document in mc['LJ40K']['tf'].find():
	e, w, c = document['emotion'], document['word'], document['count']
	D[e][w] += c

minTotalCount 

# ratio and count
R = defaultdict(lambda: Counter())

## entropy
E = {}

## get all distinct word
ws = sorted(mc['LJ40K']['tf'].distinct('word'))

for word in ws:
	S = float(sum([D[emotion][word] for emotion in D]))
	wc = []
	for emotion in D:
		count = D[emotion][word]
		ratio = count/S
		R[emotion][word] = ( count, ratio )
		wc.append(count)

	E[word] = entropy(wc)

for word in ws:
	dist = {}
	S = 0
	for emotion in R:
		(count,ratio) = R[emotion][word]
		dist[emotion] = {'count': count, 'ratio': ratio}
		S += count
	if S <= 3: continue

	doc = {}
	doc['word'] = word
	doc['entropy'] = E[word]
	doc['dist'] = dist
	doc['count'] = S
	mc['LJ40K']['words'].insert(doc)


e = sorted([ (E[w],w, [ (R[x][w][0],R[x][w][1],x) for x in R]) for w in ws], reverse=True)

minEF = 3 # minimum emotion frequency




for etpy, w, dist in e:

	S = sum([x[0] for x in dist]) # total word count
	efreq = len([x for x in dist if x[0]>0.0])
	if S > 500 and etpy > 0.0 and efreq >= minEF:
		print color.render(str(round(etpy,4)), 'r'),'\t',color.render(w,'g'),'\t',color.render(str(efreq),'y')
		show_topk = [y[2] for y in sorted(dist, key=lambda x:x[0], reverse=True)][:3]

		show = []
		# lst_dist = []

		for x in dist:

			# lst_dist.append(str(x[0]), )

			if x[0] == 0.0: 
				show.append(color.render(str(x[0]),'b'))
			else:
				
				c = 'w' if x[2] not in show_topk else 'lp'
				aux = '' if x[2] not in show_topk else '#'+color.render(x[2], 'lc')
				show.append(color.render(str(x[0]),c)+aux)
		print ','.join(show)

		# print ','.join([ if x[0] == 0.0 else  for x in dist])




