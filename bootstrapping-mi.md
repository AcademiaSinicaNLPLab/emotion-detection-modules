#Bootstrapping-MI


* Given seed

		seed = ['regret' , ... ]

* Calculate p(x)
		
		total = sum( [ doc['count'] for doc in db['WC'].find() ] )

		f(regret) = db['WC'].find_one({'word': 'regret'})['count']
		
		p(regret) = f(regret)/total
		
* save to <code>mongo > MI</code>

	* mongo structure
	
			[mongo.MI]
			doc = 
			{
				"prob" : p(regret), 
				"word" : "regret",		# word 要做 index
				"length" : 1
			}

	* update and insert if the word not found. <code>upsert</code>: <code>up</code>date + in<code>sert</code>

			db['MI'].update( {'word': 'regret'},  doc, upsert=True )
		
* Find pairs and

		sent = 'I regret that I loved you'
		
	* 程式可以這樣寫，就不用檢查 key 是否在 dict 中
	
			from collections import defaultdict, Counter
			
			D = defaultdict( lambda:Counter() )
			
			D['regret']['i'] += 1 	  # 看到 i
					...
			D['regret']['you'] += 1   # 看到 you

	* 掃完全部 sents, 得到 D
		
			D = {
				'regret':
				{
					<Counter>
					{
						'i': 2,
						'that':1,
						'loved':1,
						'you':1
					}
				},
				'seed word...'
			}
		
* 計算 mi

		scoring_method = 'mi'

		mi(i,regret) = p(i,regret)/( p(i) * p(regret) )
		
		p(i|regret) = 2 / sum( D['regret'].values() )
		
		p(i,regret) = p(i|regret) * p(regret)
		
	* 把算過的存起來
	
			[set]
			processed = set("#i#regret", ...)
		
	* 更新 <code>mongo > MI</code>
	
			[mongo.MI]
			doc = db['MI'].find_one({ 'word':'#i#regret' })
			doc = {
				"prob" : p(i, regret)
				"word" : "#i#regret"
				"length" : 2,
				"scoring": scoring_method
				"score": mi(i, regret)
			}
			
