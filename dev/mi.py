import sqlite3
import pymongo
import pickle
from collections import Counter, defaultdict

emoList = pickle.load(open('emoList.pkl', 'r'))

# read sentences from database 'db/sentence.db'
# Table: sents(emotion TEXT, docID int, sentID int, sent TEXT)
con = sqlite3.connect('db/sentence.db')
cur = con.cursor()

# connect to mongoDB
mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
co_wc = db['WC']
co_mi = db['MI']

# d = {'word': 'book', 'count': 5}
# d = {'pair': '#book#pen', 'count': 3}
# co.insert(d)
# ('book', 'pen', ...) --> '#book#pen#...'

wc = Counter()
mi = Counter()

sql = 'select * from sents'
res = cur.execute(sql).fetchall()
emotion = ''
c = 0
for row in res:
	# 
	if row[0] != emotion:
		print str(c) + ': ' + row[0]
		c += 1
		emotion = row[0]
	# 
	sent = row[3].lower()
	words = sent.split(' ')
	for i in range(len(words)):
		wc[words[i]] += 1
		for j in range(i+1, len(words)):
			pair = sorted([words[i], words[j]])
			key = '#' + pair[0] + '#' + pair[1]
			mi[key] += 1

for key in wc:
	co_wc.insert( {'word': key, 'count': wc[key]} )
for key in mi:
	co_mi.insert( {'pair': key, 'count': mi[key]} )

# sorted(['', ''])
# .lower()

def cascade_list_of_words(list_of_words):
	return '#' + '#'.join( sorted(list_of_words) )

def remove_seed(list_of_words, seed_list):
	new_list = list_of_words
	for word in seed_list:
		try:
			new_list.remove(word)
		except:
			return []
	return new_list
