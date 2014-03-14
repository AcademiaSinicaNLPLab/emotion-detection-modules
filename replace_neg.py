def replace_neg(deps_in_sentence):

	neg_words = []
	replaced = []
	for dep in deps_in_sentence:
		if dep[6] == 'neg':	neg_words.append( (dep[3], dep[5]) )
	for dep in deps_in_sentence:
		dep = list(dep)
		if (dep[3], dep[5]) in neg_words: dep[3] = '_' + dep[3]
		if (dep[7], dep[9]) in neg_words: dep[7] = '_' + dep[7]
		replaced.append(tuple(dep))
	return replaced

