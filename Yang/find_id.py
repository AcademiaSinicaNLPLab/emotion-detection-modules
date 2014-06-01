# -*-  coding: utf-8 -*-

import sys, json, os


def get_docs(corpus_path):
	docs = []
	for emotion in [e for e in os.listdir(corpus_path) if os.path.isdir(corpus_path+'/'+e)]:

		emotion_path = corpus_path + '/' + emotion
		for doc in [d for d in os.listdir(emotion_path) if not d.startswith('.')]:
			docs.append((doc, emotion))
	return docs

def build_docID(docs): return dict(enumerate(docs))


if __name__ == '__main__':

	corpus_path = '/Users/Maxis/corpus/LJ40K'

	output = 'LJ40K_docid.json'

	docs = get_docs(corpus_path)

	id_to_EmotionDoc = build_docID(docs)

	json.dump(id_to_EmotionDoc, open(output, 'w'))