#Bootstrapping-MI


###Round 1

1. Given seed

		seed = ['regret' , ... ]

2. Calculate p(x)
		
		total = sum( [ doc['count'] for doc in db['WC'].find() ] )

		f(regret) = db['WC'].find_one({'word': 'regret'})['count']
		
		p(regret) = f(regret)/total
		
3. save to <code>mongo > MI</code>

	i. mongo structure
	
			[mongo.MI]
			doc = 
			{
				"prob" : p(regret), 
				"word" : "regret",		# word 要做 index
				"length" : 1
			}

	2. update and insert if the word not found. <code>upsert</code>: <code>up</code>date + in<code>sert</code>

			db['MI'].update( {'word': 'regret'},  doc, upsert=True )
		
4. Find pairs

		sent = 'I regret that I loved you'
		
		seed: "#regret", 把 regret 刪掉
		
	要檢查的 <code>[I, that, I, loved, you]</code>
		
	i. 程式可以這樣寫，就不用檢查 key 是否在 dict 中
	
			from collections import defaultdict, Counter
			
			D = defaultdict( lambda:Counter() )
			
			D['regret']['i'] += 1 	  # 看到 i
					...
			D['regret']['you'] += 1   # 看到 you

	i. 掃完全部 sents, 得到 D
		
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
		
5. 計算 mi

		scoring_method = 'mi'

		mi(i,regret) = p(i,regret)/( p(i) * p(regret) )
		
		p(i|regret) = 2 / sum( D['regret'].values() )
		
		p(i,regret) = p(i|regret) * p(regret)
		
	i. 把算過的存起來
	
			[set]
			processed = set("#i#regret", ...)
		
	i. 更新 <code>mongo > MI</code>
	
			[mongo.MI]
			doc = db['MI'].find_one({ 'word':'#i#regret' })
			doc = {
				"prob" : p(i, regret)
				"word" : "#i#regret"
				"length" : 2,
				"scoring": scoring_method
				"score": mi(i, regret)
			}
			
---

###Round 2

1. get new seed from round 1

		seed = ['#i#regret' , ... ]

2. Calculate p(x)

3. save to <code>mongo > MI</code>

4. Find pairs

		sent = 'I regret that I loved you'
		
		seed: "#i#regret", 把 i, regret 刪掉
		
	要檢查的 <code>[that, I, loved, you]</code>
		
	i. 可以用 itertools
	
			from itertools import product

			list( product(['#i#regret'], ['that', 'I', 'loved', 'you']) )
					 
			output >
			[('#i#regret', 'that'),
		 	('#i#regret', 'I'),
			 ('#i#regret', 'loved'),
			 ('#i#regret', 'you')]