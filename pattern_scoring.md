Pattern scoring
===

* Given a pattern, we calculate its confidence score in each emotion.

	![equation](http://latex.codecogs.com/gif.latex?score%28pattern%2C%20emotion%29)

	e.g., 

	* pattern: `i am pissed`

	* occurrences:

		![image](img/dist_of_i-am-pissed.png)
	
	* idea:
	
		separate the occurrences of `emotion` and `!emotion`
		
		all emotins: [4, 6, 1, 2, ..., 1, 25, 2, 3, 2]
		
		annoyed | !annoyed |
		------------ | ------------- |
		[6] | [ 4, ~~6~~, 1, 2, ..., 1, 25, 2, 3, 2 ]  |		

		pissed oﬀ | !pissed oﬀ |
		------------ | ------------- |
		[25] | [ 4, 6,1, 2, ..., 1, ~~25~~, 2, 3, 2 ]  |	
	
		sleepy | !sleepy |
		------------ | ------------- |
		[2] | [ 4, 6,1, 2, ..., 1, 25, 2, 3, ~~2~~ ]  |		

How
===

* origin thoughts

	annoyed | !annoyed |
	------------ | ------------- |
	[6] | [ 4, ~~6~~, 1, 2, ..., 1, 25, 2, 3, 2 ]  |
	
	```python
	6 : (4+1+2+...+1+25+2+3+2)/39
	-> 6 : 1.74
	-> score("i am pissed", annoyed) = 6/(6+1.74) = 0.77
	```
	

* However, this method doesn't work:

	consider the following two cases, two totally different distribution but yield the same score

	1. Case 1:
	
		happy | !happy |
		------------ | ------------- |
		[9] | [ 1, 1, 1, ..., 1, 1 ]  |	
		
		```python
		9 : (1+1+...+1)/39
		-> 9: 1
		-> score(pattern, happy) = 0.9
		```			
	
	1. Case 2:
		
		happy | !happy |
		------------ | ------------- |
		[9] | [ 39, 0, 0, ..., 0, 0 ]  |	
		
		```python
		9 : (39+0+...+0)/39
		-> 9: 1
		-> score(pattern, happy) = 0.9 # WHAT!! This is definitely not we want!!
		```		

> How to consider the __scale__ (frequency) and the __distribution__ at the same time?
	
	
![image](img/all-1.png)

![image](img/increase.png)



