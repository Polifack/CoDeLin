# COnstituent and DEpendency LINearization system

Unified System to linearize Constituent and Pependency trees into labels to train Sequence Labeling Systems. The main goal of this system is to cast the task of Constituent and Dependency Parsing into a Sequence Labeling Task with good metrics of Speed and Accuracy. The implemented Tree Encodings are based on [Viable Dependency Parsing as Sequence Labeling](https://aclanthology.org/N19-1077.pdf), [Bracket Encodings for 2-Planar Dependency Parsing](https://aclanthology.org/2020.coling-main.223.pdf), [Constituent Parsing as Sequence Labeling](https://aclanthology.org/D18-1162v2.pdf) and [Better, Faster, Stronger Sequence Tagging Constituent Parsers](https://arxiv.org/pdf/1902.10985.pdf)

## Features

Allows for the linearization of trees using different algorithms and for two formalisms

- Constituent tree
	- Absolute encoding
	- Relative encoding
	- Dynamic encoding
	- Incremental encoding
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

The parameters available for CoDeLin are:
- Formalism: Indicates the formalism in which input data is. Values = [CONST | DEPS].
- Operation: Indicates if we want to turn trees into labels or labels into trees. Values = [ENC | DEC].
- Encoding: Indicates the encoding type that we want to use to encode/decode the input data; Values = [ABS, REL, DYN, POS, BRK, BRK_2P].
- Input file: Path of the input file to encode/decode; Value: string.
- Ouptut file: Path to save the decoded/encoded file; Value: string.
- Separator: Character or String used to separate the different fields of the encoded labels; Indicated by: --sep string.
- Part of Speech tags: Flag that if present the system will employ a part-of-speech tagging library to add POS tags to the decoded trees. By default this is not enabled. Indicated by the flag --postags.
- POS Language: Field indicating the language to use during part of speech tagging. By default is English. Indicated by --lang language_code.
- Features: Field indicating an array of features to extract during the encoding process from the source treebank and add them to the .labels output file. If certain feature does not exist for a word, by default the system will set a '_' character. Indicated by --feats feat_1, feat_2, feat_3...
- Time: Flag indicating if we should output time information

Constituent only parameters:
- Joiner: Character or String used to join the unary chains in the labels; Indicated by: --joiner string.
- Conflict: Node label conflict resolution strategy to apply during the decoding of constituent trees. The available options are take the first label, take the last or take the most repeated; Indicated by --conflict [strat_first | strat_last | start max]. Default is start_max.
- Allow nulls: Flag that if present will allow nulls in the decoded constituent tree. Indicated by --nulls.

Dependency only parameters:
- Displacement: Flag indicating to use displacement in bracket based encodings (i.e. encode the label of word w_i in l_i+1); Indicated by the flag --disp.
- Planar algorithm: Algorithm employed in 2-planar bracket based encoding; Indicated by: --planar [GREED | PROPAGATE].
- Single root: Flag that if present will post-process dependency trees to force root uniqueness. Indicated by --sroot.
- Root search: Indicates the method of root search employed in dependency parsing. The available options are take the first node with head=0 as root or take the first node with rel=0 as root; Indicated by --rsearch [start_gethead | strat_getrel]. Default is strat_gethead.


### Encode single file example:
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
### Decode single file example:
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

The generated labels from this systems are shaped in columns separated by tabulartor characters where the first column is the input token and the last one is the expected output label. The columns in-between are the indicated features.

| Input_Token   | Features      | Output|
| ------------- |:-------------:| -----:|
| Influential   | NNS           |  4_NP |
| members       | IN            |  3_PP |
| of            | DT            |  2_NP |

## Compatible Sequence Labeling Tools

The Constituent and Dependency Trees Linearization System has been tested with [NCRFpp](https://github.com/jiesutd/NCRFpp) tagger and [Machamp](https://github.com/machamp-nlp/machamp) Multi Task Learning Tagger.

## Experimental results

Results for the experiments performed with CoDeLin labels using different sequence labeling systems.

### Constituent Parsing

F-1 score and speed for the selected constituent treebanks using the different sequence labeling systems.

![F-1 const](https://raw.githubusercontent.com/Polifack/CoDeLin/main/pics/const_fscore.png)
![Speed const](https://raw.githubusercontent.com/Polifack/CoDeLin/main/pics/const_speed.png)

### Dependency Parsing

Labeled Attachment Score (LAS) and speed for the selected Universal Dependencies treebanks using the different sequence labeling systems.

![Las deps](https://raw.githubusercontent.com/Polifack/CoDeLin/main/pics/deps_las.png)
![Speed deps](https://raw.githubusercontent.com/Polifack/CoDeLin/main/pics/deps_speed.png)


## To Do List

- Option to change how the root is encoded in bracket based encoding.
- Change how root relations are encoded in relative dependency encoding.
- Change the head-selection algorithm in dependency encoding. New algorithm should be able to select head using both head field and deprel field.
- Add a new head-selection heuristic based on taking as 'root' as the node that most other nodes depend into (more outgoing arrows)
- Add a new purelly incremental constituent tree encoding. This new encoding should encode the tree using w-1 and w instead of w+1 and w. This should allow to use a single LSTM in the sequence labeling architecture [Done](https://raw.githubusercontent.com/Polifack/CoDeLin/dev/pics/incr_enc.png)
- Add head-driven phrase structure grammars as formalism. 
- Add semantic dependency parsing structure option.
- Explore the addition of Named Entity Recognition and Part of Speech Tagging to labels.
