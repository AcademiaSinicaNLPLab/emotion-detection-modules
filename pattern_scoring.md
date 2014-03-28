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

1. origin thoughts

	annoyed | !annoyed |
	------------ | ------------- |
	[6] | [ 4, ~~6~~, 1, 2, ..., 1, 25, 2, 3, 2 ]  |
	
	```
	6 : (4+1+2+...+1+25+2+3+2)/39
	
	-> 6 : 1.74
	
	-> score("i am pissed", annoyed) = 6/(6+1.74) = 0.77
	
	```
