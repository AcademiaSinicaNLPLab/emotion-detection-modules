##Pattern - 新架構！

1. ###Preprocessing

	[白板](img/new.0313.1.jpg)
	
	算出 pattern 在 training 各 emotion 中出現次數，作為 pattern scoring function 的 input
	
	```javascript
	{
		"emotion" : "pissed off",
		"pattern" : "i am pissed",
		"count" : 25
	}
	```
	
2. ###Lexicon construct

	[白板](img/new.0313.2.jpg), [程式](exicon_construction.py)
	
	套用不同的 pattern scoring function，得出一個 pattern 出現在某 emotion 中的機率

	![equation](http://latex.codecogs.com/gif.latex?f_%7BPS_%7Bk%7D%7D%20%5Cleft%28p%2C%20e%20%5Cright%20%29%20%3D%20%5Ctextrm%7Bpattern%20scoring%20function%20%7D%20k)
	```latex
	f_{PS_{k}} \left(p, e \right ) = \textrm{pattern scoring function } k
	```
	
	```javascript
	// mongo 資料結構
	{
		"emotion" : "pissed off",
		"pattern" : "i am pissed",
		"count" : 25,
		
		"prob_1": 0.8,  // use pattern scoring function 1
		"prob_2": 0.7   // use pattern scoring function 2
	}
	```
	
	```python
	# python module
	def pattern_scoring_functions(pattern, pattern_vector, emotion, function=1):
		# if function 1 ...
		# if function 2...
		return (score or prob of pattern in emotion)
	```
	
	```
	補 pattern scoring function
	...
	```
	
3. ###emotion detection

	[白板](img/new.0313.3.jpg)
	
	```
	模組 input: 文章 d + 情緒 e
	模組 output: 1 (Yes) or 0 (No)
	```
	
	1. ####考慮 significance factor (sf)
	
		把算出來的機率分數，套上 pattern 長度 (sf1), 原始句子長度 (sf2) or pattern 占句子比例 (sf3)

		![equation](http://latex.codecogs.com/gif.latex?S_%7Bd%2C%20e%7D%20%3D%20%5Comega_%7Bp%7D*sf_%7Bk%7D%20%5Cleft%28%20p%5Cright%20%29%20*prob%20%5Cleft%28p%2C%20e%20%5Cright%20%29%20%2Cp%20%5Cin%20%5Ctextrm%7Bcollection%20of%20patterns%20in%20%7D%20d)
	
		```latex
		S_{d, e} = \omega_{p}*sf_{k} \left( p\right ) *prob \left(p, e \right ) ,p \in \textrm{collection of patterns in } d
		```
		
		type | value |
		------------ | ------------- |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B0%7D) | 1  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B1%7D) | ![equation](http://latex.codecogs.com/gif.latex?%7Cp%7C)  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B2%7D) | ![equation](http://latex.codecogs.com/gif.latex?1/%7Csent%7C)  |
		![equation](http://latex.codecogs.com/gif.latex?sf_%7B3%7D) | ![equation](http://latex.codecogs.com/gif.latex?sf_%7B1%7D) * ![equation](http://latex.codecogs.com/gif.latex?sf_%7B2%7D)  |
	
	1. ####計算一篇文章 (i.e., 一堆 patterns ) 的分數
	
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
	
	```
	補 document scoring function
	...
	```

4. ###evaluation

	[白板](img/new.0313.4.jpg)
	
	
