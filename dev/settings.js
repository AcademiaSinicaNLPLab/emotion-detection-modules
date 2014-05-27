keyword 
	// kw-bag
	{ "_id" : ObjectId("53744c12d4388c206b2cc881"), "keyword_type" : "basic", "lemma" : false }
	{ "_id" : ObjectId("53744d55d4388c49faffe9b5"), "keyword_type" : "extend", "lemma" : false }
	{ "_id" : ObjectId("53745053d4388c3fc1579c2a"), "keyword_type" : "basic", "lemma" : true }
--> { "_id" : ObjectId("537451d1d4388c7843516ba4"), "keyword_type" : "extend", "lemma" : true }

keyword_position 
	// kw-bag-pos
	{ "_id" : ObjectId("537dd9afd4388c2a1adf8ca2"), "keyword_type" : "basic", "lemma" : false, "section" : "b20_m60_e20" }
--> { "_id" : ObjectId("537ddc3ad4388c4fb8dbe1ae"), "keyword_type" : "extend", "lemma" : true, "section" : "b20_m60_e20" }

keyword_emotion 
	// kw-emo-b
	{ "_id" : ObjectId("537dad77d4388c409cff30bb"), "keyword_type" : "basic", "lemma" : false }
--> { "_id" : ObjectId("537ec46bd4388c72b5877f67"), "keyword_type" : "extend", "lemma" : true }

keyword_emotion_position 
	// kw-emo-b-pos
--> { "_id" : ObjectId("53820bd2d4388c3907e06819"), "keyword_type" : "extend", "lemma" : true, "section" : "b20_m60_e20" }

// ------------------------------------------------------------------------------------------------------------ //

pattern 
	// pat-bag
	{ "_id" : ObjectId("5373115dd4388c6e5d884e49"), "min_count" : 1 }
	{ "_id" : ObjectId("5373109ed4388c55dbf8fc51"), "min_count" : 2 }
	{ "_id" : ObjectId("53730f67d4388c27cc4c06f1"), "min_count" : 3 }
	{ "_id" : ObjectId("537c6be9d4388c5b46f646a6"), "min_count" : 5 }
--> { "_id" : ObjectId("537c6c90d4388c0e27069e7b"), "min_count" : 10 }

pattern_position 
	// pat-bag-pos
	{ "_id" : ObjectId("5381edaed4388c4ffaeda288"), "min_count" : 1, "section" : "b20_m60_e20" }
	{ "_id" : ObjectId("5381ef94d4388c613e7da12f"), "min_count" : 2, "section" : "b20_m60_e20" }
	{ "_id" : ObjectId("5381f11cd4388c566ff04479"), "min_count" : 3, "section" : "b20_m60_e20" }
	{ "_id" : ObjectId("5381f244d4388c260d8146ce"), "min_count" : 5, "section" : "b20_m60_e20" }
--> { "_id" : ObjectId("5381f342d4388c7060e645c1"), "min_count" : 10, "section" : "b20_m60_e20" }

pattern_emotion 
	// pat-emo-b
	{ "_id" : ObjectId("537d838fd4388c3735dc1916"), "counting_unit_type" : 0, "feature_value_type" : 4 }	// binary
--> { "_id" : ObjectId("5382fa27d4388c23417ddc53"), "feature_value_type" : 5 }	// binary, 		min_count: 4
	// pat-emo-f
	{ "_id" : ObjectId("5384154bd4388c0b59bd9b58"), "feature_value_type" : 6 }	// frequency, 	min_count: 4
	{ "_id" : ObjectId("538449c8d4388c2e5ded6d45"), "feature_value_type" : 7 }	// frequency, 	min_count: 4, 	cut: true
	{ "_id" : ObjectId("538450b1d4388c6fba995dc0"), "feature_value_type" : 8 }	// frequency, 	min_count: 10
	{ "_id" : ObjectId("53845312d4388c2826e7adf5"), "feature_value_type" : 9 }	// frequency, 	min_count: 10, 	cut: true

pattern_emotion_position 
	// pat-emo-b-pos
	{ "_id" : ObjectId("5379d6a5d4388c6a09110bb7"), "counting_unit_type" : 0, "feature_value_type" : 4, "section" : "b20_m60_e20" }	// binary
	{ "_id" : ObjectId("5379fe4fd4388c110be4cd06"), "counting_unit_type" : 0, "feature_value_type" : 5, "section" : "b20_m60_e20" }	// binary, 	min_count: 4
	// pat-emo-f-pos
	{ "_id" : ObjectId("5384467dd4388c1ca3785cb1"), "section" : "b20_m60_e20", "feature_value_type" : 6 }	// frequency, 	min_count: 4
	{ "_id" : ObjectId("538448d4d4388c5e9ab2cbb8"), "section" : "b20_m60_e20", "feature_value_type" : 7 }	// frequency, 	min_count: 4, 	cut: true
	{ "_id" : ObjectId("53845f1ad4388c0a6b20f2e2"), "section" : "b20_m60_e20", "feature_value_type" : 8 }	// frequency, 	min_count: 10
	{ "_id" : ObjectId("538461aed4388c4a0663584c"), "section" : "b20_m60_e20", "feature_value_type" : 9 }	// frequency, 	min_count: 10, 	cut: true

// ------------------------------------------------------------------------------------------------------------ //

fusion
	{ "_id" : ObjectId("538302743681df11cd509c77"), "sources" : "537451d1d4388c7843516ba4,537c6c90d4388c0e27069e7b" }
	{ "_id" : ObjectId("538302893681df167c63717f"), "sources" : "537ddc3ad4388c4fb8dbe1ae,5381f342d4388c7060e645c1" }
	{ "_id" : ObjectId("538303fed4388c06fea2104c"), "sources" : "537d838fd4388c3735dc1916,537ec46bd4388c72b5877f67" }
	{ "_id" : ObjectId("53840d98d4388c5e8c3468ee"), "sources" : "5379fe4fd4388c110be4cd06,53820bd2d4388c3907e06819" }
	{ "_id" : ObjectId("53842e2ad4388c0d6aed7d48"), "sources" : "537451d1d4388c7843516ba4,5379fe4fd4388c110be4cd06" }
	{ "_id" : ObjectId("53842e77d4388c2461796189"), "sources" : "537451d1d4388c7843516ba4,5382fa27d4388c23417ddc53" }

