###Pattern

* #### Pattern 產生

	scenario: verb + \< subj, obj, prep_obj \>
	
	status: be_verb + adj
		

* #### Pattern 結構
	
	1. `Semantic roles`：主詞、受詞
	2. `人稱`：John --> SUBJ_3
	3. `時態`：had --> have

	
* #### Pattern 分數

	1. 長 pattern --> 高分

		<pre>sent: I really wish I <u>have</u> someone ...
	    SV: <b>i have</b>
	   SVO: <b>i have someone</b>
	  Args: <b>wish i have someone</b> </pre>
	  
	  * pattern長度
	  * pattern長度/sentence長度
		

	2. pf, df or pf-idf
 
	3. Multiple Lexicons
	
		* <b>Lexicon_Happy</b>: `Prob(pattern, Happy)`
		* <b>Lexicon_Sad</b>: `Prob(pattern, Sad)`
		* ...
		* <b>Lexicon_Anger</b>: `Prob(pattern, Anger)`
	
	
		---
		
			p1 < Prob(p1, Happy), Prob(p1, Sad), ..., Prob(p1, Anger) >
			
			p2 < Prob(p2, Happy), Prob(p2, Sad), ..., Prob(p2, Anger) >
			
			...
			
			pk < Prob(pk, Happy), Prob(pk, Sad), ..., Prob(pk, Anger) >
		
		
		---
		
		* #####predict as _True_ if prob > 0.5 else _False_
		
				p1 < 0, 1, ..., 1 >
	
				p2 < 1, 1, ..., 1 >		
	
				...

				pk < 1, 0, ..., 0 >	

* ###To do

	* #####[ testing ] pattern占sentence的比例 (固定一種結構)
	
	* #####[ testing ] pattern占sentence的比例 (多種結構)

	* #####[ testing ] pattern的長度 (多種結構) 

	* ##### `done` [ preprocessing ] mongo sentences, deps 加 unique id
	
		* udocID: 0 ~ 39,999
		* usentID: 0 ~ 937,143

		* 找 特定句子 (usentID = 100) [\[mongo structure\]](pattern.md#lj40k--sents)
			```python
			db['deps'].find( { 'usentID': 100 } )
			```

		* 找 一篇文章 (udocID = 0) 中的所有 dependency [\[mongo structure\]](pattern.md#lj40k--deps)
			```python
			db['deps'].find( { 'udocID': 0 } )
			```
	
	* ##### `done` [ training + testing ] 統一有一個抽 pattern 的模組，抽出一篇文章所有的 pattern，記錄規則 (prep, subj, obj, cop, ...)。做 n-fold 可以用這邊篩選文章的 pattern [\[mongo structure\]](pattern.md#lj40k--pats)

	* ##### 建 40 個 binary lexicon
	
		* micro/macro average
		
		* 利用已知類別的資訊, 考慮這兩種:
		
			1. 如果全部都集中在某一類，而且那一類不是 Happy，平均下去可能就不顯著	
			
					[ 10,  0,    ..., 100,    0   ] -->  Happy: _Happy = 10: 100  --> _Happy

					[ 10,  0/39, ..., 100/39, 0/39] -->  Happy: _Happy = 10: 2.56 --> Happy

			1. 如果都很分散，但都不是 Happy

					[ 10,  5,    ..., 5,    5   ] -->  Happy: _Happy = 10: 195  --> _Happy

					[ 10,  5/39, ..., 5/39, 5/39] -->  Happy: _Happy = 10: 5    --> Happy			
			

	
	* ##### Formulate scoring functions 
	
		[CodeCogs](http://latex.codecogs.com/): convert LaTex into images

		1. **Pattern**
		
			![equation](http://latex.codecogs.com/gif.latex?score%20%5Cleft%20%28%20p_%7Bi%7D%2C%20e_%7Bj%7D%20%5Cright%20%29%20%3D%20%5Csum_%7Bd%20%5Cin%20e_%7Bj%7D%20%7D%20f%5Cleft%20%28%20p_%7Bi%7D%2C%20d%20%5Cright%20%29)
			```latex
			% 一個 pattern 在某個 emotion 中的分數
			score \left ( p_{i}, e_{j} \right ) = \sum_{d \in e_{j} } f\left ( p_{i}, d \right )
			```
			*f*: pattern 在某情緒中的總出現次數
			
			*e*: document collection, a set of documents with certain emotion

			*d*: a document

		2. **Document**
		
			![equation](http://latex.codecogs.com/gif.latex?%5Cbar%7Bd%7D_%7Bi%7D%20%3D%20%5Cleft%20%5B%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B1%7D%20%5Cright%20%29%2C%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B2%7D%20%5Cright%20%29%2C%20...%2C%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B40%7D%20%5Cright%20%29%20%5Cright%20%5D)
			```latex
			% 一個 document 的 40 個分數
			\bar{d}_{i} = \left [ prob\left ( d_{i}, e_{1} \right ), prob\left ( d_{i}, e_{2} \right ), ..., prob\left ( d_{i}, e_{40} \right ) \right ]
			```

* [討論照片](img/discuss.jpg)

--------------------------

* ####database

	* ######LJ40K > pats
	
		index: `udocID`, `usentID`

		```javascript
		{
			"_id" : ObjectId("531e8ba13681df1329f74705"),
			
			"udocID" : 37,
			"usentID" : 734,
			"emotion" : "accomplished",
			"sent_length" : 34,
			
			"anchor" : "__depressed",
			"anchor_idx" : 30,
			"anchor_type" : "JJ",
			
			"pattern" : "i am __depressed",
			"pattern_length" : 3,
			"rule" : {
				"cop" : 1,
				"subj" : 1
			},
			"weight" : 1
		}
		```
		```javascript
		{
			"_id" : ObjectId("531eb5e33681df14af39be08"),
			
			"udocID" : 12,
			"usentID" : 247,
			"emotion" : "accomplished",
			"sent_length" : 20,
			
			"anchor" : "talk",
			"anchor_idx" : 6,
			"anchor_type" : "VB",
			
			"pattern" : "people talk with me",
			"pattern_length" : 4,
			"rule" : {
				"obj" : 0,
				"subj" : 1,
				"prep" : 1
			},
			"weight" : 1,
		}
		```

	* ######LJ40K > sents
	
		index: `udocID`, `usentID`

		```javascript
		{
			"_id" : ObjectId("531944ac3681dfca09875205"),
			"emotion" : "accomplished",
			"udocID" : 0,
			"usentID" : 0,
			
			"sent_length" : 10,
			"sent_pos" : "I/PRP got/VBD new/JJ hair/NN :/: O/RB omfg/VBG I/PRP love/VBP it/PRP",
			"sent" : "I got new hair : O omfg I love it"
		}
		```
	* ######LJ40K > mapping

		```javascript
		{
		        "_id" : ObjectId("52fc4aa93681df69081246f5"),
		        "docID" : 0,
		        "emotion" : "accomplished",
		        "local_docID" : 0,
		        "path" : "LJ40K/accomplished/0.txt"
		}
		```
	* ######LJ40K > patterns (舊的)
	
		```javascript
		{
			"_id" : ObjectId("5305729f3681dfda4a9c52d5"),
			"pattern": "you given me",
			"structure": "SVO",
			"df": [<40 elements>],
			"ndf": [<40 elements>],
			"pf": [<40 elements>],
			"npf": [<40 elements>]
		}
		```
	* ######LJ40K > deps
	
		index: `udocID`, `usentID`
	
		```javascript
		{
			"_id" : ObjectId("531944ac3681dfca098751fc"),
			
			"emotion" : "accomplished",
			"udocID" : 0,
			"usentID" : 0,
			"sent_length" : 10,
				
			"rel" : "nsubj",
			"x" : "got",
			"xIdx" : 2,
			"xPos" : "VBD",
			
			"y" : "I",
			"yIdx" : 1,
			"yPos" : "PRP"
		}
		```
* ####容易發生的小 bugs
	

	1. 縮寫：'re `(are)`，'ll `(will)`
	2. 大小寫：You, you


