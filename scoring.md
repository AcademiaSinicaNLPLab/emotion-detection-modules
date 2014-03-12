# Scoring 	function 

[CodeCogs](http://latex.codecogs.com/): convert LaTex into images

###Pattern
---

* 一個 pattern 的 40 個分數

	![equation](http://latex.codecogs.com/gif.latex?%5Cbar%7Bp%7D_%7Bi%7D%20%3D%20%5Cleft%20%5B%20score%5Cleft%20%28%20p_%7Bi%7D%2C%20e_%7B1%7D%20%5Cright%20%29%2C%20score%5Cleft%20%28%20p_%7Bi%7D%2C%20e_%7B2%7D%20%5Cright%20%29%2C%20...%2C%20score%5Cleft%20%28%20p_%7Bi%7D%2C%20e_%7B40%7D%20%5Cright%20%29%20%5Cright%20%5D)
	
	```latex
	\bar{p}_{i} = \left [ score\left ( p_{i}, e_{1} \right ), score\left ( p_{i}, e_{2} \right ), ..., score\left ( p_{i}, e_{40} \right ) \right ]
	```

* 某 pattern 在特定 emotion 中的分數
	
	![equation](http://latex.codecogs.com/gif.latex?score%20%5Cleft%20%28%20p_%7Bi%7D%2C%20e_%7Bj%7D%20%5Cright%20%29%20%3D%20%5Csum_%7Bd%20%5Cin%20e_%7Bj%7D%20%7D%20f%5Cleft%20%28%20p_%7Bi%7D%2C%20d%20%5Cright%20%29)
	
	```latex
	score \left ( p_{i}, e_{j} \right ) = \sum_{d \in e_{j} } f\left ( p_{i}, d \right )
	```
	
	* _f_: pattern 在某情緒中的總出現次數 
	* _e_: document collection, a set of documents with certain emotion 
	* _d_: a document

### Document
---

* 一個 document 的 40 個分數

	![equation](http://latex.codecogs.com/gif.latex?%5Cbar%7Bd%7D_%7Bi%7D%20%3D%20%5Cleft%20%5B%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B1%7D%20%5Cright%20%29%2C%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B2%7D%20%5Cright%20%29%2C%20...%2C%20prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7B40%7D%20%5Cright%20%29%20%5Cright%20%5D)
	
	```latex
	\bar{d}_{i} = \left [ prob\left ( d_{i}, e_{1} \right ), prob\left ( d_{i}, e_{2} \right ), ..., prob\left ( d_{i}, e_{40} \right ) \right ]
	```
	
* 某篇 document 被判定成特定 emotion 的機率
	
	![equation](http://latex.codecogs.com/gif.latex?prob%5Cleft%20%28%20d_%7Bi%7D%2C%20e_%7Bj%7D%20%5Cright%20%29%20%3D)
	
	```latex
	prob\left ( d_{i}, e_{j} \right ) =
	```
	
* 加入分布資訊
	
	* 標準差 ![equation](http://latex.codecogs.com/gif.latex?%5CDelta_%7B%5Coverline%7Bp_%7Bi%7D%7D%7D)
		
	* Entropy ![equation](http://latex.codecogs.com/gif.latex?%5Cvarepsilon_%7B%5Coverline%7Bp_%7Bi%7D%7D%7D)
	
	* example:

		考慮兩種 pattern

		![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26p_%7B1%7D%20%3D%20%5Cleft%20%5B%20%5C%7B10%20%5C%7D%2C%20%5C%7B0%2C%20...%2C%200%2C%20...%2C100%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7Bp_%7B1%7D%7D%7D%3D%2015.81%2C%20%5Cvarepsilon_%7B%5Coverline%7Bp_%7B1%7D%7D%7D%20%3D0%20%5C%5C%20%26p_%7B2%7D%20%3D%20%5Cleft%20%5B%20%5C%7B10%5C%7D%2C%20%5C%7B9%2C%20...%2C%2010%2C...%2C%2011%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7Bp_%7B2%7D%7D%7D%3D%200.98%2C%20%5Cvarepsilon_%7B%5Coverline%7Bp_%7B2%7D%7D%7D%20%3D%205.27%20%5Cend%7Balign*%7D)
		
		```latex
		% P2: 19個 9, 1 個 10, 19 個 11
		\begin{align*} &p_{1} = \left [ \{10 \}, \{0, ..., 0, ...,100\} \right], \Delta_{\overline{p_{1}}}= 15.81, \varepsilon_{\overline{p_{1}}} =0 \\ &p_{2} = \left [ \{10\}, \{9, ..., 10,..., 11\} \right], \Delta_{\overline{p_{2}}}= 0.98, \varepsilon_{\overline{p_{2}}} = 5.27 \end{align*}
		```
	
		加起來
	
		![equation](http://latex.codecogs.com/gif.latex?p_%7B3%7D%20%3D%20%5Cleft%20%5B%20%5C%7B20%5C%7D%2C%20%5C%7B9%2C%20...%2C%2010%2C%20...%2C111%20%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7Bp_%7B3%7D%7D%7D%3D%2015.99%2C%20%5Cvarepsilon_%7B%5Coverline%7Bp_%7B1%7D%7D%7D%20%3D4.82)
	
		```latex
		p_{3} = \left [ \{20\}, \{9, ..., 10, ...,111 \} \right], \Delta_{\overline{p_{3}}}= 15.99, \varepsilon_{\overline{p_{1}}} =4.82
		```

---

[< back](pattern.md)