###Pattern

* #### Pattern 產生

	verb + \< subj, obj, prep_obj, be_adj \>
		

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
	
				pk < 1, 0, ..., 0 >	


---

* 截圖

	![image](img/discuss.jpg) 



* ####容易發生的小 bugs
	

	1. 縮寫：'re `(are)`，'ll `(will)`
	2. 大小寫：You, you


