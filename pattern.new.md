##Pattern - 新架構！

1. Preprocessing

	```javascript
	{
		pat: i __love you,
		emotion: sad,
		count: 10
	}
	```
2. Lexicon construct

	
3. emotion detection

	![equation](http://latex.codecogs.com/gif.latex?S_%7Bd%2C%20e%7D%20%3D%20%5Comega_%7Bp%7D*sf_%7Bk%7D%20%5Cleft%28%20p%5Cright%20%29%20*prob%20%5Cleft%28p%2C%20e%20%5Cright%20%29%20%2Cp%20%5Cin%20%5Ctextrm%7Bcollection%20of%20patterns%20in%20%7D%20d)
	
	```latex
	S_{d, e} = \omega_{p}*sf_{k} \left( p\right ) *prob \left(p, e \right ) ,p \in \textrm{collection of patterns in } d
	```
	
	![equation](http://latex.codecogs.com/gif.latex?f_%7BDS%7D%20%5Cleft%20%28%20S_%7Bd%2C%20e%7D%5Cright%20%29%20%3D%20%5Cfrac%7B%5Csum_%7Bs%20%5Cin%20S_%7Bd%2C%20e%7D%7D%20s%7D%7B%5Cleft%20%7C%20S_%7Bd%2C%20e%7D%20%5Cright%20%7C%7D)
	
	```latex
	f_{DS} \left ( S_{d, e}\right ) = \frac{\sum_{s \in S_{d, e}} s}{\left | S_{d, e} \right |}
	```
	
	![eqaution](http://latex.codecogs.com/gif.latex?docscore%20%5Cleft%28%20d%2C%20e%20%5Cright%20%29%20%3D%20%5Cleft%5C%7B%5Cbegin%7Bmatrix%7D%20%26%201%2C%20f_%7BDS%7D%20%5Cleft%28%20S_%7Bd%2C%20e%7D%20%5Cright%20%29%20%5Cgeq%20%5Cepsilon%20%5C%5C%20%26%200%2C%20f_%7BDS%7D%20%5Cleft%28%20S_%7Bd%2C%20e%7D%20%5Cright%20%29%20%3C%20%5Cepsilon%20%5Cend%7Bmatrix%7D%5Cright.)
	
	```latex
	docscore \left( d, e \right ) = \left\{\begin{matrix} & 1, f_{DS} \left( S_{d, e} \right ) \geq \epsilon \\ & 0, f_{DS} \left( S_{d, e} \right ) < \epsilon \end{matrix}\right.
	```
4. evaluation
