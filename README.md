# Constituent and Dependency Trees Linearization System

Unified System to linearize Constituent and Pependency trees into labels to train Sequence Labeling Systems. The main goal of this system is to cast the task of Constituent and Dependency Parsing into a Sequence Labeling Task with good metrics of Speed and Accuracy. The implemented Tree Encodings are based on [Viable Dependency Parsing as Sequence Labeling](https://aclanthology.org/N19-1077.pdf), [Bracket Encodings for 2-Planar Dependency Parsing](https://aclanthology.org/2020.coling-main.223.pdf), [Constituent Parsing as Sequence Labeling](https://aclanthology.org/D18-1162v2.pdf) and [Better, Faster, Stronger Sequence Tagging Constituent Parsers](https://arxiv.org/pdf/1902.10985.pdf)

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

Also, for bracket encoding in dependency trees can split the tree in two planes using two different algorithms:

- Greedy Planar Separation
- Propagation Planar Separation

## Usage

Can be used to encode single files with encode_const.py or encode_deps.py respectively or decode single files with decode_const.py or decode_deps.py

### Encode single file:
```
$ python3.8 main.py
	CONST
	ENC
	ABS
	test.trees
	test.labels
	--time
	--sep _
	--ujoiner +
	--feats lem ADM ASP AZP BIZ
$ python3.8 main.py 
	DEPS
	ENC
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
$ python3.8 main.py
	CONST
	DEC
	ABS
	test.labels
	test_decoded.trees
	--time
	--sep _
	--ujoiner +
	--conflict C_STRAT_MAX

$ python3.8 decode_deps.py 
	DEPS
	DEC
	BRK_2P
	test.labels
	test_decoded.conllu
	--time
	--sep _
	--disp
```

## Output Format

The generated labels from this systems are in the standard [Beginning, Inside, Outside](https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)) format, where the first column is the input token and the last one is the expected output label

| Input_Token   | Features      | Output|
| ------------- |:-------------:| -----:|
| Influential   | NNS           |  4_NP |
| members       | IN            |  3_PP |
| of            | DT            |  2_NP |

## Compatible Sequence Labeling Tools

The Constituent and Dependency Trees Linearization System has been tested with [https://github.com/jiesutd/NCRFpp](NCRFpp) tagger and [https://github.com/machamp-nlp/machamp](Machamp) Multi Task Learning Tagger. 

