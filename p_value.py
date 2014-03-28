from collections import defaultdict
import json, pickle

Plist = []

doc = open('pvalue.txt').read()
Z2 = map(lambda x:float(x), doc.split('\n')[0].split('\t')[1:])

for line in doc.split('\n')[1:]:
	if not line: continue
	z_1 = float(line.split('\t')[0])
	p_values = map(lambda x:float(x), line.split('\t')[1:])
	for z_2, p in zip(Z2, p_values):
		zvalue = round(z_1+z_2, 2)
		negzvalue = zvalue*-1.0
		Plist.append( (zvalue, p) )
		Plist.append( (negzvalue,round(1.0-p,4)) )


Plist.sort()

Pdict = dict(Plist)

json.dump(Plist, open('P-value.list.json','w'))
pickle.dump(Pdict, open('P-value.dict.pkl','w'))