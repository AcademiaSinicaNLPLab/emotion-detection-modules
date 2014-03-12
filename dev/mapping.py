import pymongo, sqlite3, json, pickle
from itertools import product

sqldb_path = '/home/cherry/projects/emotionDetection/db/sentence.db'

con = sqlite3.connect(sqldb_path)
cur = con.cursor()

mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
db = mc['LJ40K']
emotions = sorted([x['emotion'] for x in list(db['emotions'].find({'label':'LJ40K'}))])

pairs = list(product(emotions, range(1000)))

no_docID = []
sql = 'select sentID, sent from sents where emotion = ? and docID = ?'
for emotion, ldocID in pairs:
	sres = cur.execute(sql, (emotion, ldocID) ).fetchall()
	if len(sres) == 0: no_docID.append(emotion, ldocID)
	else:
		lsentID = 0
		for sentID, sent in sres:
			
			mres = db['sents'].find( {'emotion': emotion, 'sent': sent}, {'_id':0, 'udocID':1, 'usentID':1, 'sent_length':1} )
			if mres.count() == 1: # sure this is the sentence
				mres = db['sents'].find( {'emotion': emotion } )
				break
			lsentID += 1



# 給 emotion, ldocID --> 抓出一篇
# 第一句 --> 找到一個 --> stop
# 	  --> 找到多個 --> 下一句

# 掃完全部句子 --> 


from collections import Counter
sql = 'select sentID, sent from sents where emotion = ? and docID = ?'
def find_map(emotion, ldocID):
	sres = cur.execute(sql, [emotion, ldocID] ).fetchall()
	C = Counter(reduce(lambda x,y: x+y, [[mdoc['udocID'] for mdoc in db['sents'].find( { 'emotion': emotion, 'sent': sent } )] for sentID, sent in sres]))
	possible = [udocID for udocID in C if C[udocID] == len(sres)]
	print emotion, ldocID, '-->', possible

# bored|701|0|You Are 19 Years Old 19 Under 12 : You are a kid at heart
# bored|701|1|You still have an optimistic life view - and you look at the world with awe.13-19 : You are a teenager at heart
# bored|701|2|You question authority and are still trying to find your place in this world.20-29 : You are a twentysomething at heart
# bored|701|3|You feel excited about what 's to come . .
# bored|701|4|love , work , and new experiences.30-39 : You are a thirtysomething at heart
# bored|701|5|You 've had a taste of success and true love , but you want more ! 40 + : You are a mature adult
# bored|701|6|You 've been through most of the ups and downs of life already
# bored|701|7|Now you get to sit back and relax . What Age Do You Act ?

# (bored, sent) --> mongo --> [ud1: 1, ud2: 4, ud3: 8]







