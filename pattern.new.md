##Pattern - 新架構！

* #### Steps
 	1. [pattern extraction](#pattern-extraction)
	1. [Lexicon construction](#lexicon-construction)
	2. [Pattern scoring](#pattern-scoring)
	3. [Document scoring (emotion detection)](#document-scoring-emotion-detection)
	4. [Evaluation](#evaluation)

* #### To-do-list
	
	* [討論照片](img/discuss.0318.jpg)

	1. 改 pattern scoring 公式（[程式](pattern_scoring.py)、[數學式](#pattern-scoring)） [方程式編輯器](http://latex.codecogs.com/)
	
	1. 改 [mongo structure](#%E8%B3%87%E6%96%99%E7%B5%90%E6%A7%8B)
		1. patscore 把分數放在一起
		2. cfg 合併成字串
		3. patscore.scoring 改成 patscore.ps_function
	
	1. 把流程包起來

---

* ###Pattern extraction

	[extract_pattern.py](extract_pattern.py)
	
	* anchor: __verb__, __adj__
	* structure
	 	- event: [subj, __verb__, obj, prep_obj]
	 	- state: [subj, be, __adj__] 

* ###Lexicon construction

	`training`

	[白板](img/new.0313.1.jpg), [lexicon_construction.py](lexicon_construction.py)
	
	算出 pattern 在 training 各 emotion 中出現次數，作為 pattern scoring function 的 input
	
	```javascript
	// mongo.lexicon: pattern occurrence
	> db.lexicon.findOne({pattern: 'i am pissed', emotion: 'pissed off'})
	{
		"emotion" : "pissed off",
		"pattern" : "i am pissed",
		"count" : 25
	}
	```
	
* ###Pattern scoring

	`training`
	
	[白板](img/new.0313.2.jpg), [[新公式]](img/discuss.0318.jpg), [pattern_scoring.py](pattern_scoring.py), 
	
	套用不同的 pattern scoring function (`ps_function`)，得出一個 pattern 出現在某 emotion 中的 ~~機率~~ 分數

	* #### 定義 pattern scoring function
		
		pattern scoring function k

		![equation](http://latex.codecogs.com/gif.latex?f_%7BPS_%7Bk%7D%7D%20%5Cleft%28p%2C%20e%20%5Cright%20%29%20%3D%20%5Cfrac%7Bscore_%7Bk%7D%20%5Cleft%20%28%20p%2C%20e%20%5Cright%20%29%7D%7Bscore_%7Bk%7D%20%5Cleft%20%28%20p%2C%20e%20%5Cright%20%29%20&plus;%20score_%7Bk%7D%20%5Cleft%20%28%20p%2C%20%5Coverline%7B%20e%20%7D%20%5Cright%20%29%7D)
		```latex
		f_{PS_{k}} \left(p, e \right ) = \frac{score_{k} \left ( p, e \right )}{score_{k} \left ( p, e \right ) + score_{k} \left ( p, \overline{ e } \right )}
		```
		where
	
		![equation](http://latex.codecogs.com/gif.latex?score_%7Bi%7D%20%5Cleft%20%28%20p%2C%20e%20%5Cright%20%29%20%3D%20%5Csum_%7Bd%20%5Ctextrm%7B%20annotated%20as%20%7D%20e%20%7D%20occur%5Cleft%20%28%20p%2C%20d%20%5Cright%20%29)
		```latex
		score_{i} \left ( p, e \right ) = \sum_{d \textrm{ annotated as } e } occur\left ( p, d \right )
		```
	
		![equation](http://latex.codecogs.com/gif.latex?score_%7B0%7D%20%5Cleft%20%28%20p%2C%5Coverline%7Be%7D%20%5Cright%20%29%20%3D%20%5Cfrac%7B%5Csum_%7B%20e_j%20%5Cin%20%5Coverline%7Be_l%7D%20%7D%20score%5Cleft%20%28%20p%2C%20e_%7Bj%7D%20%5Cright%20%29%7D%7B%5Cleft%20%7C%20%5Coverline%7Be%7D%20%5Cright%20%7C%7D)
		```latex
		score_{0} \left ( p,\overline{e} \right ) = \frac{\sum_{ e_j \in \overline{e_l} } score\left ( p, e_{j} \right )}{\left | \overline{e} \right |}
		```
	
		![equation](http://latex.codecogs.com/gif.latex?score_%7B1%7D%20%5Cleft%20%28%20p%2C%5Coverline%7Be%7D%20%5Cright%20%29%20%3D%20score_%7B0%7D%20%5Cleft%20%28%20p%2C%5Coverline%7Be%7D%20%5Cright%20%29%20*%20%5CDelta_%7B%20%5Coverline%7Bnp%7D%20%7D)
		```latex
		score_{1} \left ( p,\overline{e} \right ) = score_{0} \left ( p,\overline{e} \right ) * \Delta_{ \overline{np} }
		```
	
		![equation](http://latex.codecogs.com/gif.latex?score_%7B2%7D%20%5Cleft%20%28%20p%2C%5Coverline%7Be%7D%20%5Cright%20%29%20%3D%20score_%7B0%7D%20%5Cleft%20%28%20p%2C%5Coverline%7Be%7D%20%5Cright%20%29%20*%20%5Cleft%28%201%20&plus;%20%5Calpha%20*%20%5CDelta_%7B%20%5Coverline%7Bnp%7D%20%7D%20%5Cright%20%29)
		```latex
		score_{2} \left ( p,\overline{e} \right ) = score_{0} \left ( p,\overline{e} \right ) * \left( 1 + \alpha * \Delta_{ \overline{np} } \right )
		```	
	
	* #### 資料結構
 
		* current `db.patscore`
		
			```javascript
			// db.patscore: pattern scores（跑完 scoring function 後的結果）
			{
			        "emotion" : "crazy",
			        "pattern" : "i am pissed",
			        "prob" : 0.9669999980078527,
			        "scoring" : 1,
			        "smoothing" : 0
			},
			{
			        "emotion" : "crazy",
			        "pattern" : "i am pissed",
			        "prob" : 0.6223404255319149,
			        "scoring" : 0,
			        "smoothing" : 0
			}
			```
		* to-do `db.patscore`
		
			```javascript
			// db.patscore: pattern scores  (output of ps_function)
			{
				"emotion": "crazy",
				"pattern": "i am pissed",
				"cfg": "fs_function=1,smoothing=0",
				"score": 0.9669999980078527
			},
			{
				"emotion": "crazy",
				"pattern": "i am pissed",
				"cfg": "fs_function=1,smoothing=0",
				"score": 0.9669999980078527
			}
			```


		* 從程式裡用新方法跑出 prob 後 update mongo
			```python
			mc = pymongo.Connection('doraemon.iis.sinica.edu.tw')
			patscore = mc['LJ40K']['patscore']
			
			probs = pattern_scoring_function(pattern, function, smoothing_method)
			
			## update prob of pattern "i am pissed" in emotion "pissed off" using scoring function 1, smoothing method: 0
			patscore.update( { 'emotion': 'pissed off', 'pattern': 'i am pissed', 'scoring': 1, 'smoothing': 0 }, { '$set': { 'prob': prob } } )
		```
	
* ###Document scoring (emotion detection)

	`testing`

	[白板](img/new.0313.3.jpg), [document_scoring.py](document_scoring.py)
	
	```
	模組 input: 文章 d + 情緒 e
	模組 output: 1 (Yes) or 0 (No)
	```
	
	1. ####Event scoring: 考慮 significance factor (sf)
	
		sf: 把算出來的機率分數，套上 pattern 長度 (sf1), 句子長度 (sf2) or pattern 占句子比例 (sf3)

		![equation](http://latex.codecogs.com/gif.latex?S_%7Bd%2C%20e%7D%20%3D%20weight_%7Bp%7D*sf_%7Bk%7D%20%5Cleft%28%20p%5Cright%20%29%20*prob%20%5Cleft%28p%2C%20e%20%5Cright%20%29%20%2Cp%20%5Cin%20%5Ctextrm%7Bcollection%20of%20patterns%20in%20%7D%20d)
	
		```latex
		S_{d, e} = weight_{p}*sf_{k} \left( p\right ) *prob \left(p, e \right ) ,p \in \textrm{collection of patterns in } d
		```
		
		type | value |
		------------ | ------------- |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B0%7D) | 1  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B1%7D) | ![equation](http://latex.codecogs.com/gif.latex?%7Cp%7C)  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B2%7D) | ![equation](http://latex.codecogs.com/gif.latex?1/%7Csent%7C)  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B3%7D) | ![equation](http://latex.codecogs.com/gif.latex?sf_%7B1%7D) * ![equation](http://latex.codecogs.com/gif.latex?sf_%7B2%7D)  |

		```python
		def significance_factor(pat, sig_function):
			if sig_function == 0: return 1
			if sig_function == 1: return pat['pattern_length']
			if sig_function == 2: return float(1)/pat['sent_length']
			if sig_function == 3: return pat['pattern_length'] * ( float(1)/pat['sent_length'] )
		```
		
		```python
		def event_scoring(pat, emotion, opt, sig_function):
			# build query
			query = {'pattern': pat['pattern'].lower(), 'emotion': emotion}
			query.update(opt)  # add entries in opt: scoring: 1, smoothing: 0
			
			# fetch pattern score from mongo collection "patscore"
			res = co_patscore.find_one( query )
			prob_p_e = 0.0 if not res else res['prob']
			
			return pat['weight'] * sigFactor(pat, sig_function) * prob_p_e
		```

	
	2. ####Document scoring: 計算一篇文章 (i.e., 一堆 patterns ) 的分數
	
		given a document _d_ in emotion _e_, 
	
		document scoring function：幾何平均, 算數平均, ...etc. (e.g., 算數平均)
	
		![equation](http://latex.codecogs.com/gif.latex?f_%7BDS%7D%20%5Cleft%20%28%20S_%7Bd%2C%20e%7D%5Cright%20%29%20%3D%20%5Cfrac%7B%5Csum_%7Bs%20%5Cin%20S_%7Bd%2C%20e%7D%7D%20s%7D%7B%5Cleft%20%7C%20S_%7Bd%2C%20e%7D%20%5Cright%20%7C%7D)
	
		```latex
		f_{DS} \left ( S_{d, e}\right ) = \frac{\sum_{s \in S_{d, e}} s}{\left | S_{d, e} \right |}
		```
	
		將一篇文章打上 score，如果 score > 0.5 (可調), 就判定是情緒 e (i.e., output 1)
	
		![eqaution](http://latex.codecogs.com/gif.latex?docscore%20%5Cleft%28%20d%2C%20e%20%5Cright%20%29%20%3D%20%5Cleft%5C%7B%5Cbegin%7Bmatrix%7D%20%26%201%2C%20f_%7BDS%7D%20%5Cleft%28%20S_%7Bd%2C%20e%7D%20%5Cright%20%29%20%5Cgeq%20%5Cepsilon%20%5C%5C%20%26%200%2C%20f_%7BDS%7D%20%5Cleft%28%20S_%7Bd%2C%20e%7D%20%5Cright%20%29%20%3C%20%5Cepsilon%20%5Cend%7Bmatrix%7D%5Cright.)
	
		```latex
		docscore \left( d, e \right ) = \left\{\begin{matrix} & 1, f_{DS} \left( S_{d, e} \right ) \geq \epsilon \\ & 0, f_{DS} \left( S_{d, e} \right ) < \epsilon \end{matrix}\right.
		```
		
		```python
		def document_scoring(udocID, emotion, epsilon, ds_function, opt, sig_function): 
			mDocs = list( co_pats.find( {'udocID': udocID} ) ) 
			# arithmetic mean
			if ds_function == 1:
				docscore = sum( event_scoring(pat, emotion, opt, sig_function) for pat in mDocs ) / len(mDocs)
				return 1 if docscore >= epsilon else 0
			# geometric mean
			if ds_function == 2:
			...
		```
		
		mongo db.docscores 資料結構
		```javascript
		{
			// query
			udocID: 35000,
			gold_emotion: 'pissed off',
			test_emotion: 'pissed off',
			ds_function: 1,
			ps_function: 0,
			smoothing: 0,
	
			// results
			docscore: 0.95,
			predict: 1
		}
		```
* ###Evaluation

	[白板](img/new.0313.4.jpg), [evaluation.py](evaluation.py)
	
	```python
	# 用 cfg 來選擇 test instance
	cfg = {
		'ds_function': 1,
		'ps_function': 1,
		'smoothing':  0,
		'sig_function': 0,
		'epsilon':  0.5	
	}
	```
	
	- 產生 test file, 記錄用某個設定的 predict 結果 [[output]](#-test_instances)
	```python
	def gen_test(cfg) 
	```
	- 計算 true/false positive/negative, accuracy, P,R,F [[output]](#-results)
	```python
	def eval(cfg, output='accuracy')
	```	
	
	###### * test_instances
	
	```javascript
	> db.test_instances.findOne()
	{
	        "_id" : ObjectId("5326b8c918db058cd1826c77"),
	        "ds_function" : 1,
	        "epsilon" : 0.5,
	        "gold_emotion" : "accomplished",
	        "predict" : {
	                "crazy" : 1,
	                "pissed off" : 1,
	                "tired" : 1,
	                "exhausted" : 1,
	                "sleepy" : 1,
	                "confused" : 1,
	                "sad" : 1,
	                "cheerful" : 1,
	                "blah" : 1,
	                "bouncy" : 1,
	                "lonely" : 1,
	                "blank" : 1,
	                "cold" : 1,
	                "busy" : 1,
	                "drained" : 1,
	                "hopeful" : 1,
	                "creative" : 1,
	                "content" : 1,
	                "contemplative" : 1,
	                "calm" : 1,
	                "sick" : 1,
	                "bored" : 1,
	                "frustrated" : 1,
	                "excited" : 1,
	                "happy" : 1,
	                "good" : 1,
	                "okay" : 1,
	                "ecstatic" : 1,
	                "loved" : 1,
	                "crushed" : 1,
	                "crappy" : 1,
	                "awake" : 1,
	                "aggravated" : 1,
	                "depressed" : 1,
	                "hungry" : 1,
	                "amused" : 1,
	                "anxious" : 1,
	                "accomplished" : 1,
	                "chipper" : 1,
	                "annoyed" : 1
	        },
	        "ps_function" : 1,
	        "sig_function" : 0,
	        "smoothing" : 0,
	        "udocID" : 800
	}	
	```
	
	###### * results
	
	```javascript
	> db.results.findOne()
	{
	        "_id" : ObjectId("5327a22618db058cd1828bb7"),
	        "accuracy" : 0.4869,
	        "ds_function" : 1,
	        "emotion" : "accomplished",
	        "epsilon" : 0.5,
	        "f1" : 0.48849539406345954,
	        "precision" : 0.487,
	        "ps_function" : 1,
	        "ratio" : 39,
	        "recall" : 0.49,
	        "res" : {
	                "TN" : 3774,
	                "FP" : 4026,
	                "FN" : 102,
	                "TP" : 98
	        },
	        "sig_function" : 0,
	        "smoothing" : 0
	}
	```

