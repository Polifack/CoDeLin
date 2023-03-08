# **CO**nstituent and **DE**pendency **LIN**earization system

Unified System to linearize Constituent and Dependency trees into labels to employ with Sequence Labeling Systems. The implemented Tree Encodings are based on [Viable Dependency Parsing as Sequence Labeling](https://aclanthology.org/N19-1077.pdf), [Bracket Encodings for 2-Planar Dependency Parsing](https://aclanthology.org/2020.coling-main.223.pdf), [Constituent Parsing as Sequence Labeling](https://aclanthology.org/D18-1162v2.pdf) and [Better, Faster, Stronger Sequence Tagging Constituent Parsers](https://arxiv.org/pdf/1902.10985.pdf). Link to [colab demo.](https://colab.research.google.com/drive/1Oso7tlxGgDrP40i8BUT6hCiybG1qvTkP?usp=sharing)

## Features

Allows for the linearization of trees using different algorithms and for two formalisms

- Constituent tree
	- **ABS**olute encoding
	- **REL**ative encoding
	- **DYN**amic encoding
	- **INC**remental encoding
- Dependency tree
	- **ABS**olute encoding
	- **REL**ative encoding
	- **POS** based encoding
	- **BR**ac**K**et encoding

Also, for bracket encoding in dependency trees can split the tree in two planes using two different algorithms:

- **GREED**y Planar Separation
- **PROP**agation Planar Separation

## Usage

CoDeLin as a library:

- Constituent Trees linearization and decoding:
```python

	from src.models.const_tree import C_Tree
	from src.utils.constants import C_STRAT_FIRST
	from src.encs.enc_const import *

	original_tree = "(S (NP (DT The) (NNS owls)) (VP (VBP are) (RB not) (SBAR (WHNP (WP what)) (S (NP (PRP they)) (VP (VBP seem))))) (PUNCT .))"
	
	c_tree = C_Tree.from_string(original_tree)
	
	encoder = C_NaiveAbsoluteEncoding(separator="_", unary_joiner="+")
	
	lc_tree = encoder.encode(c_tree)

	c_tree = encoder.decode(lc_tree)
	c_tree.postprocess_tree(conflict_strat=C_STRAT_FIRST,clean_nulls=True)

		
```

- Dependency Trees linearization and decoding:

```python
	
	from src.models.deps_tree import D_Tree
	from src.encs.enc_deps import *
	from src.utils.constants import D_ROOT_HEAD

	conllu_sample = "# sent_id = 1\n"+\
	"# text = The owls are not what they seem.\n"+\
	"1\tThe\tthe\tDET\tDT\tDefinite=Def|PronType=Art\t2\tdet\t_\t_\n"+\
	"2\towls\towl\tNOUN\tNNS\tNumber=Plur\t3\tnsubj\t_\t_\n"+\
	"3\tare\tbe\tAUX\tVBP\tMood=Ind|Tense=Pres|VerbForm=Fin\t0\troot\t_\t_\n"+\
	"4\tnot\tnot\tPART\tRB\t_\t3\tadvmod\t_\t_\n"+\
	"5\twhat\twhat\tPRON\tWP\tPronType=Int\t6\tnsubj\t_\t_\n"+\
	"6\tthey\tthey\tPRON\tPRP\tCase=Nom|Number=Plur|Person=3|PronType=Prs\t3\tparataxis\t_\t_\n"+\
	"7\tseem\tseem\tVERB\tVBP\tMood=Ind|Tense=Pres|VerbForm=Fin\t6\tccomp\t_\t_\n"+\
	"8\t.\t.\tPUNCT\t.\t_\t3\tpunct\t_\t_"

	f_idx_dict={"Number":0,"Mood":1,"PronType":2,"Tense":3,"VerbForm":4, "Person":5, "VerbForm":6, "Definite":7, "Case":8}

	d_tree = D_Tree.from_string(conllu_sample)
	
	encoder = D_NaiveAbsoluteEncoding(separator="_")
	
	ld_tree = encoder.encode(d_tree)
	
	dc_tree = encoder.decode(ld_tree)
	dc_tree.postprocess_tree(search_root_strat=D_ROOT_HEAD, allow_multi_roots=False)
	
```

Main.py allows CoDeLin to be used from command lines to encode or decode single files. The parameters available for CoDeLin are:
- **Formalism**: Indicates the formalism in which input data is. Values = [CONST | DEPS].
- **Operation**: Indicates if we want to turn trees into labels or labels into trees. Values = [ENC | DEC].
- **Encoding**: Indicates the encoding type that we want to use to encode/decode the input data; Values = [ABS, REL, DYN, POS, BRK, BRK_2P].
- **Input file**: Path of the input file to encode/decode; Value: string.
- **Ouptut file**: Path to save the decoded/encoded file; Value: string.
- **Separator**: Character or String used to separate the different fields of the encoded labels; Indicated by: --sep string.
- **Part of Speech**: Flag that if present the system will employ a part-of-speech tagging library to add POS tags to the decoded trees. By default this is not enabled. Indicated by the flag --postags.
- **POS Language**: Field indicating the language to use during part of speech tagging. By default is English. Indicated by --lang language_code.
- **Features**: Field indicating an array of features to extract during the encoding process from the source treebank and add them to the .labels output file. If certain feature does not exist for a word, by default the system will set a '_' character. Indicated by --feats feat_1, feat_2, feat_3...
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
- Hfr: Flag indicating to encode root dependencies in relative encoding as a special label (e.g. encode '-NONE-_root' instead of '-3_root')


### Encode single file example:
```bash
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
```bash
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

- [x] Change how root relations are encoded in relative dependency encoding.
- [x] Add a new purelly incremental constituent tree encoding. This new encoding should encode the tree using w-1 and w instead of w+1 and w. This should allow to use a single LSTM in the sequence labeling architecture [Sample](https://raw.githubusercontent.com/Polifack/CoDeLin/pics/incr_enc.png)
- [ ] Change the head-selection algorithm in dependency encoding. New algorithm should be able to select head using both head field and deprel field.
- [ ] Add a new head-selection heuristic based on taking as 'root' as the node that most other nodes depend into (more outgoing arrows)
- [ ] Add head-driven phrase structure grammars as formalism. 
- [ ] Add semantic dependency parsing structure option.
- [ ] Explore tetra-tagging as a encoding for constituent parsing.
- [ ] Implement discontinous trees linearization
- [ ] Allow for outputting more than one encoding per file (i.e. having more than one output column where each column is a label for a different encoding)
- [ ] Explore the addition of Named Entity Recognition taks using linearized parsing.
