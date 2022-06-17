# Tree linearization

## Features

Allows for the linearization of trees using different algorithms and for two formalisms

- Constituent tree
	- Absolute encoding
	- Relative encoding
	- Dynamic encoding
- Dependency tree
	- Absolute encoding
	- Relative encoding
	- POS based encoding
	- Bracket encoding

Also, for bracket encoding in dependency trees can split the tree in two planes using two different algorithms

## Usage

Can be used to encode single files with encode_const.py or encode_deps.py respectively or decode single files with decode_const.py or decode_deps.py

### Encode single file:
```
$ python3.8 encode_const.py 
	ABS
	test.trees
	test.labels
	--time
	--sep _
	--ujoiner +
	--feats lem ADM ASP AZP BIZ
$ python3.8 encode_deps.py 
	BRK_2P
	test.labels
	test.trees
	--time
	--sep _
	--disp
	--planar GREED
	--feats c g m mwehead
```
### Decode single file
```
$ python3.8 decode_const.py
	ABS
	test.labels
	test_decoded.trees
	--time
	--sep _
	--ujoiner +
	--conflict C_STRAT_MAX

$ python3.8 decode_deps.py 
	BRK_2P
	test.labels
	test_decoded.conllu
	--time
	--sep _
	--disp
```