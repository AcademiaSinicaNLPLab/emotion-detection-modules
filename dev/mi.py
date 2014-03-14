import sqlite3
import pymongo
import pickle
from collections import Counter
from itertools import groupby

emoList = pickle.load(open('emoList.pkl', 'r'))

con = sqlite3.connect('db/sentence.db')
cur = con.cursor()
# sents(emotion TEXT, docID int, sentID int, sent TEXT)

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co_wc = db['WC']
co_mi = db['MI']
# d = {'word': 'book', 'count': 5}
# d = {'pair': '#book#pen', 'count': 3}
# co.insert(d)
# ('#book', 'pen') --> '##book#pen'

wc = Counter()
mi = Counter()

sql = 'select * from sents'
res = cur.execute(sql).fetchall()
emotion = ''
c = 0
for row in res:
	if row[0] != emotion:
		print str(c) + ': ' + row[0]
		c += 1
		emotion = row[0]
	sent = row[3]
	words = sent.split(' ')
	for i in range(len(words)):
		wc[words[i].lower()] += 1
		for j in range(i+1, len(words)):
			pair = sorted([words[i].lower(), words[j].lower()])
			key = '#' + pair[0] + '#' + pair[1]
			mi[key] += 1

for key in wc:
	co_wc.insert( {'word': key, 'count': wc[key]} )
for key in mi:
	co_mi.insert( {'pair': key, 'count': mi[key]} )

# sorted(['', ''])
# .lower()

