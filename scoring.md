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
		* 先對 occurrence vector 做完 normalization 再取標準差
		* std( [ 1,  2,  3] ) = 0.816
		* std( [10, 20, 30] ) = 8.16
		
	* Entropy ![equation](http://latex.codecogs.com/gif.latex?%5Cvarepsilon_%7B%5Coverline%7Bp_%7Bi%7D%7D%7D)
	
	* example:

		考慮 document d  
		兩種 pattern p1, p2  
		( np1: normalized p1, np2: normalized p2 )

		![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26p_%7B1%7D%20%3D%20%5Cleft%20%5B%20%5C%7B10%20%5C%7D%2C%20%5C%7B0%2C%20...%2C%200%2C%20...%2C100%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7Bp_%7B1%7D%7D%7D%3D%2015.81%2C%20%5CDelta_%7B%5Coverline%7Bnp_%7B1%7D%7D%7D%3D%200.15806%2C%20%5Cvarepsilon_%7B%5Coverline%7Bp_%7B1%7D%7D%7D%20%3D0%20%5C%5C%20%26p_%7B2%7D%20%3D%20%5Cleft%20%5B%20%5C%7B10%5C%7D%2C%20%5C%7B9%2C%20...%2C%2010%2C...%2C%2011%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7Bp_%7B2%7D%7D%7D%3D%200.98%2C%20%5CDelta_%7B%5Coverline%7Bnp_%7B2%7D%7D%7D%3D%200.00253%2C%20%5Cvarepsilon_%7B%5Coverline%7Bp_%7B2%7D%7D%7D%20%3D%205.27%20%5Cend%7Balign*%7D)
		
		```latex
		% P2: 19個 9, 1 個 10, 19 個 11
		\begin{align*} &p_{1} = \left [ \{10 \}, \{0, ..., 0, ...,100\} \right], \Delta_{\overline{p_{1}}}= 15.81, \Delta_{\overline{np_{1}}}= 0.15806, \varepsilon_{\overline{p_{1}}} =0 \\ &p_{2} = \left [ \{10\}, \{9, ..., 10,..., 11\} \right], \Delta_{\overline{p_{2}}}= 0.98, \Delta_{\overline{np_{2}}}= 0.00253, \varepsilon_{\overline{p_{2}}} = 5.27 \end{align*}
		```
	
		p1, p2平均
	
		![equation](http://latex.codecogs.com/gif.latex?%5Cfrac%7B%20p_%7B1%7D%20&plus;%20p_%7B2%7D%20%7D%7B2%7D%20%3D%20%5Cleft%20%5B%20%5C%7B%5Cfrac%7B20%7D%7B2%7D%5C%7D%20%2C%20%5C%7B%5Cfrac%7B9%7D%7B2%7D%2C%20...%2C%20%5Cfrac%7B10%7D%7B2%7D%2C%20...%2C%5Cfrac%7B111%7D%7B2%7D%20%5C%7D%20%5Cright%5D%2C%20%5CDelta_%7B%5Coverline%7B%5Cfrac%7B%20p_%7B1%7D%20&plus;%20p_%7B2%7D%20%7D%7B2%7D%20%7D%7D%3D%208.00%2C%20%5Cvarepsilon_%7B%5Coverline%7B%5Cfrac%7B%20p_%7B1%7D%20&plus;%20p_%7B2%7D%20%7D%7B2%7D%20%7D%7D%20%3D4.83)
		
		```latex
		\frac{ p_{1} + p_{2} }{2} = \left [ \{\frac{20}{2}\} , \{\frac{9}{2}, ..., \frac{10}{2}, ...,\frac{111}{2} \} \right], \Delta_{\overline{\frac{ p_{1} + p_{2} }{2} }}= 8.00, \varepsilon_{\overline{\frac{ p_{1} + p_{2} }{2} }} =4.83
		```
		
		pattern *k* 在 happy (emotion *l* ) 中的分數
		
		![equation](http://latex.codecogs.com/gif.latex?score%5Cleft%20%28%20p_%7Bk%7D%2C%20e_%7Bl%7D%20%5Cright%20%29)
		```latex
		score\left ( p_{k}, e_{l} \right )
		```
		
		pattern *k* 在 非 happy 中的分數
		
		![equation](http://latex.codecogs.com/gif.latex?%5Csum_%7B%20j%20%5Cin%20%5C%5B1%3A40%20%5C%5D%2C%20j%5Cneq%20l%20%7D%20score%5Cleft%20%28%20p_%7Bk%7D%2C%20e_%7Bj%7D%20%5Cright%20%29)
		
		```latex
		\sum_{ j \in \[1:40 \], j\neq l } score\left ( p_{k}, e_{j} \right )
		```
		
		* Case 1 用 local 標準差
		
			![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26%5Comega_%7Bp_%7B1%7D%7D%20%3D%20p_%7B1%7D%28happy%2C%20%5Coverline%7Bhappy%7D%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%20score%5Cleft%20%28%20p_%7B1%7D%2Chappy%20%5Cright%20%29%2C%20score%5Cleft%20%28%20p_%7B1%7D%2C%5Coverline%7Bhappy%7D%20%5Cright%20%29%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%20score%5Cleft%20%28%20p_%7B1%7D%2Chappy%20%5Cright%20%29%2C%20%5Cfrac%7B%5Csum_%7Be%20%5Cin%20%5Coverline%7Bhappy%7D%20%7D%20score%5Cleft%20%28%20p_%7B1%7D%2C%20e%20%5Cright%20%29%7D%7B%20%5Cleft%20%7C%20%5Coverline%7Bhappy%7D%20%5Cright%20%7C%20%7D%20*%20%5CDelta%20%5Coverline%7Bp_%7B1%7D%7D%20%5Cright%20%29%5C%5C%20%26%3D%20%5Cleft%20%28%2010%2C%20%5Cfrac%7B100%7D%7B39%7D%20*%2015.8%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%2010%2C%2040.51%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%200.19%2C%200.81%20%5Cright%20%29%20%5C%5C%20%5Cend%7Balign*%7D)
			```latex
			\begin{align*} &\omega_{p_{1}} = p_{1}(happy, \overline{happy}) \\ &= \left ( score\left ( p_{1},happy \right ), score\left ( p_{1},\overline{happy} \right ) \right ) \\ &= \left ( score\left ( p_{1},happy \right ), \frac{\sum_{e \in \overline{happy} } score\left ( p_{1}, e \right )}{ \left | \overline{happy} \right | } * \Delta \overline{p_{1}} \right )\\ &= \left ( 10, \frac{100}{39} * 15.8 \right ) \\ &= \left ( 10, 40.51 \right ) \\ &= \left ( 0.19, 0.81 \right ) \\ \end{align*}
			```
			![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26%5Comega_%7Bp_%7B2%7D%7D%20%3Dp_%7B2%7D%28happy%2C%20%5Coverline%7Bhappy%7D%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%2010%2C%20%5Cfrac%7B390%7D%7B39%7D%20*%200.98%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%2010%2C%209.8%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%200.51%2C%200.49%20%5Cright%20%29%20%5C%5C%20%5Cend%7Balign*%7D)
			
			```latex
			\begin{align*} &\omega_{p_{2}} =p_{2}(happy, \overline{happy}) \\ &= \left ( 10, \frac{390}{39} * 0.98 \right ) \\ &= \left ( 10, 9.8 \right ) \\ &= \left ( 0.51, 0.49 \right ) \\ \end{align*}
			```
			
			sqrt(0.19*0.51) = 0.31
			
			* 比例做 `算術平均`
			
				![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26d%28happy%2C%20%5Coverline%7Bhappy%7D%29%20%5C%5C%20%26%3D%20%5Cfrac%7B%20%5Csum_%7Bp%20%5Cin%20P%7D%20%5Comega_%7Bp%7D%20%7D%7B%20%5Cleft%20%7C%20P%20%5Cright%20%7C%20%7D%20%5C%5C%20%26%3D%20%5Cfrac%7B%20%5Comega_%7Bp_%7B1%7D%7D%20&plus;%20%5Comega_%7Bp_%7B2%7D%7D%20%7D%7B%202%20%7D%20%5C%5C%20%26%3D%20%5Cleft%20%28%20%5Cfrac%7B0.19&plus;0.51%7D%7B2%7D%2C%20%5Cfrac%7B0.81&plus;0.49%7D%7B2%7D%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%200.35%2C%200.65%20%5Cright%20%29%20%5C%5C%20%5Cend%7Balign*%7D)
				```latex
				\begin{align*} &d(happy, \overline{happy}) \\ &= \frac{ \sum_{p \in P} \omega_{p} }{ \left | P \right | } \\ &= \frac{ \omega_{p_{1}} + \omega_{p_{2}} }{ 2 } \\ &= \left ( \frac{0.19+0.51}{2}, \frac{0.81+0.49}{2} \right ) \\ &= \left ( 0.35, 0.65 \right ) \\ \end{align*}
				```
			* 比例做 `幾何平均`

				![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26d%28happy%2C%20%5Coverline%7Bhappy%7D%29%20%5C%5C%20%26%3D%20%5Csqrt%5B%5Cleft%20%7C%20P%20%5Cright%20%7C%5D%7B%5Cprod_%7Bp%20%5Cin%20P%7D%20%5Comega_%7Bp%7D%7D%20%5C%5C%20%26%3D%20%5Csqrt%7B%20%5Comega_%7Bp_%7B1%7D%7D%20*%20%5Comega_%7Bp_%7B2%7D%7D%20%7D%20%5C%5C%20%26%3D%20%5Cleft%20%28%20%5Csqrt%7B0.19*0.51%7D%2C%20%5Csqrt%7B0.81*0.49%7D%20%5Cright%20%29%20%5C%5C%20%26%3D%20%5Cleft%20%28%200.31%2C%200.63%20%5Cright%20%29%20%5C%5C%20%5Cend%7Balign*%7D)

				```latex
				\begin{align*} &d(happy, \overline{happy}) \\ &= \sqrt[\left | P \right |]{\prod_{p \in P} \omega_{p}} \\ &= \sqrt{ \omega_{p_{1}} * \omega_{p_{2}} } \\ &= \left ( \sqrt{0.19*0.51}, \sqrt{0.81*0.49} \right ) \\ &= \left ( 0.31, 0.63 \right ) \\ \end{align*}
				```
				
		* Case 2 用 global 標準差
		
			![equation](http://latex.codecogs.com/gif.latex?%5Cbegin%7Balign*%7D%20%26d%28happy%2C%20%5Coverline%7Bhappy%7D%29%20%5C%5C%20%26%3D%20d%5Cleft%20%28%20score%5Cleft%20%28%20%5Cfrac%7Bp_%7B1%7D%20&plus;%20p_%7B2%7D%7D%7B2%7D%2Chappy%20%5Cright%29%2C%20score%5Cleft%20%28%20%5Cfrac%7Bp_%7B1%7D%20&plus;%20p_%7B2%7D%7D%7B2%7D%2C%5Coverline%7Bhappy%7D%20%5Cright%20%29%20%5Cright%20%29%20%5C%5C%20%26%3D%20d%5Cleft%20%28%20%5Cfrac%7B10%7D%7B2%7D%2C%20%5Cfrac%7B%5Cfrac%7B490%7D%7B39%7D%7D%7B2%7D%20*%208.00%5Cright%20%29%20%5C%5C%20%26%3D%20d%5Cleft%285%2C%206.28%5Cright%29%20%5C%5C%20%26%3D%20d%5Cleft%28%200.44%2C%200.56%5Cright%29%20%5C%5C%20%5Cend%7Balign*%7D)
			```latex
			\begin{align*} &d(happy, \overline{happy}) \\ &= d\left ( score\left ( \frac{p_{1} + p_{2}}{2},happy \right), score\left ( \frac{p_{1} + p_{2}}{2},\overline{happy} \right ) \right ) \\ &= d\left ( \frac{10}{2}, \frac{\frac{490}{39}}{2} * 8.00\right ) \\ &= d\left(5, 6.28\right) \\ &= d\left( 0.44, 0.56\right) \\ \end{align*}
			```
---

[< back](pattern.md)
