import pickle
import sqlite3
import pymongo
from itertools import groupby
from ListCombination import ListCombination as listComb
from collections import defaultdict
from pkl2txt import pkl2txt 
import replace_neg


class sPatCreation:
	'''
		sPatCreation = structuredPat.sPatCreation('dependency_all.db', 'emoList.pkl', 'pat_.pkl', 'pat__lex.pkl')
	'''

	def __init__(self, dataBase, emoListPath, outPklPath, outLexPklPath, outLexTxtPath):
		self.con = sqlite3.connect(dataBase)
		self.cur = self.con.cursor()

		self.emoList = pickle.load(open(emoListPath, 'r'))
		self.outPklPath = outPklPath
		self.outLexPklPath = outLexPklPath
		self.outLexTxtPath = outLexTxtPath

		self.D_temp = dict()
		self.D = dict()
		self.pattern = list()

		self.emoN = 40
		self.docN = 800

	def create_Args_pat(self, PERSON=False, NEGATION=False, LEMMATIZATION=False):

		for _emoID in range(self.emoN):
			pats_in_emo = list()
			for _docID in range(self.docN):
				pats_in_doc = list()
				print 'emo(' + str(_emoID) + '): ' + self.emoList[_emoID] + ', docID: ' + str(_docID)
				sql = 'select * from deps where emotion = ? and docID = ?'
				res = self.cur.execute(sql, (self.emoList[_emoID], _docID)).fetchall()
				
				patInDoc = set()
				last_sent_ID = -1
				for _sentID, group in groupby(res, lambda x: x[2]):
					group = list(group)
					## person
					if PERSON:
						group = replace_subj_verb.replace_subj_verb(group)
					## negation
					if NEGATION:
						group = replace_neg.replace_neg(group)
					## lemmatization
					if LEMMATIZATION:
						group = replace_lemma.replace_lemma(group)

					while _sentID != (last_sent_ID + 1): 
						pats_in_doc.append([])
						last_sent_ID += 1
					pats_in_sent = list()
					for _vIdx, subgroup in groupby(group, lambda y: y[5]):
						words = list()
						verb = ('', -1)
						for row in subgroup:	
							if verb[1] == -1:
								verb = ( str(row[3]), row[5] )
								# print verb
								# raw_input()
							words.append( ( str(row[7]), row[9] ) )
						words.append( verb )
						words.sort(key = lambda x: x[1])						
						pat = [ x[0] for x in words ]
						pats_in_sent.append(pat)
						pat_str = ' '.join(pat)
						patInDoc.add(pat_str)
						if self.D.has_key(pat_str):
							self.D[pat_str][_emoID] += 1
						elif self.D_temp.has_key(pat_str):
							self.D_temp[pat_str][_emoID] += 1
						else:
							self.D_temp[pat_str] = [0]*80
							self.D_temp[pat_str][_emoID] += 1
					pats_in_doc.append(pats_in_sent)
					last_sent_ID += 1
				for p in patInDoc:
					if self.D.has_key(p):
						self.D[p][40 + _emoID] += 1
					elif self.D_temp.has_key(p):
						self.D_temp[p][40 + _emoID] += 1
						if sum( self.D_temp[pat_str][40:80] ) > 3:
							self.D[pat_str] = self.D_temp[pat_str]
				pats_in_emo.append(pats_in_doc)
			self.pattern.append(pats_in_emo)

		print 'dumping pickles ...'
		with open(self.outPklPath, 'w') as f_w1:
			pickle.dump(self.pattern, f_w1)
		with open(self.outLexPklPath, 'w') as f_w2:
			pickle.dump(self.D, f_w2)
		p2t = pkl2txt(self.emoList, self.outLexPklPath, self.outLexTxtPath)
		p2t.print_to_txt()

	def create_sPat(self, collect_rel, fixorder, linkingverb=False, PERSON=False, NEGATION=False, LEMMATIZATION=False):
		'''
			SVO:	collect_rel = ['subj','obj'], fixorder = ['subj','verb','obj']
			SV:		collect_rel = ['subj'], fixorder = ['subj','verb']
			VO:		collect_rel = ['obj'], fixorder = ['verb','obj']
			SVC:	collect_rel = ['subj','cop'], fixorder = ['subj','cop','verb']
			VR:		collect_rel = ['advmod'], fixorder = ['verb', 'advmod']

		'''
		for _emoID in range(self.emoN):
			pats_in_emo = list()
			for _docID in range(self.docN):
				pats_in_doc = list()
				print 'emo(' + str(_emoID) + '): ' + self.emoList[_emoID] + ', docID: ' + str(_docID)
				sql = 'select * from deps where emotion = ? and docID = ?'
				res = self.cur.execute(sql, (self.emoList[_emoID], _docID)).fetchall()
				
				patInDoc = set()
				last_sent_ID = -1
				for _sentID, group in groupby(res, lambda x: x[2]):
					while _sentID != (last_sent_ID + 1): 
						pats_in_doc.append([])
						last_sent_ID += 1
					pats_in_sent = list()
					group = list(group)
					## person
					if PERSON:
						group = replace_subj_verb.replace_subj_verb(group)
					## negation
					if NEGATION:
						group = replace_neg.replace_neg(group)
					## lemmatization
					if LEMMATIZATION:
						group = replace_lemma.replace_lemma(group)

					## group verb deps
					verb_deps = defaultdict(list)
					if linkingverb:
						anchors = []
						for row in group:
							if row[6] == 'cop':
								anchor = (row[3], row[5])
								anchors.append(anchor)
						for (a_word, a_idx) in anchors:
							cop_deps = [(row[6], row[7], row[9]) for row in group if row[3] == a_word and row[5] == a_idx]
							verb_deps[(a_word, a_idx)] = cop_deps
					else:
						for row in group:
							if row[4].startswith('V'):
								vi = (row[3], row[5])
								wi = (row[7], row[9])
							elif row[8].startswith('V'):
								vi = (row[7], row[9])
								wi = (row[3], row[5])
							else:
								continue
							verb_deps[vi].append( (row[6], wi[0], wi[1]) )
					## extract SVO
					for vi in verb_deps:
						D = defaultdict(list)
						if len(verb_deps[vi]) == 0: continue
						for dep_rel, word, widx in verb_deps[vi]:
							for rel in collect_rel:
								if rel in dep_rel:
									D[rel].append( word )
						if len(D) != len(collect_rel): continue
						## if equal
						(verb, vidx) = vi
						D['verb'] = [verb]
						pats = listComb([D[r] for r in fixorder])

						for pat in pats:
							pats_in_sent.append(pat)
							pat_str = ' '.join(pat)
							patInDoc.add(pat_str)
							if self.D.has_key(pat_str):
								self.D[pat_str][_emoID] += 1
							elif self.D_temp.has_key(pat_str):
								self.D_temp[pat_str][_emoID] += 1
							else:
								self.D_temp[pat_str] = [0]*80
								self.D_temp[pat_str][_emoID] += 1
					pats_in_doc.append(pats_in_sent)
					last_sent_ID += 1
				for p in patInDoc:
					if self.D.has_key(p):
						self.D[p][40 + _emoID] += 1
					elif self.D_temp.has_key(p):
						self.D_temp[p][40 + _emoID] += 1
						if sum( self.D_temp[pat_str][40:80] ) > 3:
							self.D[pat_str] = self.D_temp[pat_str]
				pats_in_emo.append(pats_in_doc)
			self.pattern.append(pats_in_emo)

		print 'dumping pickles ...'
		with open(self.outPklPath, 'w') as f_w1:
			pickle.dump(self.pattern, f_w1)
		with open(self.outLexPklPath, 'w') as f_w2:
			pickle.dump(self.D, f_w2)
		p2t = pkl2txt(self.emoList, self.outLexPklPath, self.outLexTxtPath)
		p2t.print_to_txt()


if __name__ == '__main__':
	# # Args
	# sPatCreation = sPatCreation('db/dependency.db', 'emoList.pkl', 'Args/pat_Args.pkl', 'Args/pat_Args_lex.pkl', 'Args/pat_Args_lex.txt')
	# sPatCreation.create_Args_pat(PERSON=False, NEGATION=False, LEMMATIZATION=True)

	# # sPat
	# sPatCreation = sPatCreation('db/dependency.db', 'emoList.pkl', 'VR/pat_VR.pkl', 'VR/pat_VR_lex.pkl', 'VR/pat_VR_lex.txt')
	# sPatCreation.create_sPat(collect_rel = ['advmod'], fixorder = ['verb', 'advmod'], linkingverb=False, PERSON=False, NEGATION=True, LEMMATIZATION=False)
	
	# sPat (cop)
	sPatCreation = sPatCreation('db/dependency_all.db', 'emoList.pkl', 'SVC/pat_SVC.pkl', 'SVC/pat_SVC_lex.pkl', 'SVC/pat_SVC_lex.txt')
	sPatCreation.create_sPat(collect_rel = ['subj','cop'], fixorder = ['subj','cop','verb'], linkingverb=True, PERSON=False, NEGATION=True, LEMMATIZATION=False)
