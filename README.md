# **CO**nstituent and **DE**pendency **LIN**earization system

Unified System to linearize Constituent and Dependency trees into labels to employ with Sequence Labeling Systems. The implemented Tree Encodings are based on [Viable Dependency Parsing as Sequence Labeling](https://aclanthology.org/N19-1077.pdf), [Bracket Encodings for 2-Planar Dependency Parsing](https://aclanthology.org/2020.coling-main.223.pdf), [Constituent Parsing as Sequence Labeling](https://aclanthology.org/D18-1162v2.pdf) and [Better, Faster, Stronger Sequence Tagging Constituent Parsers](https://arxiv.org/pdf/1902.10985.pdf)

## Features

Allows for the linearization of trees using different algorithms and for two formalisms

- Constituent tree
	- **ABS** (Absolute encoding)
	- **REL** (Relative encoding)
	- **DYN** (Dynamic encoding)
	- **GAP** (Gaps based encoding)
	- **4EC** (Tetra-tagging)
	- **JUX** (Attach-Juxtapose encoding)
- Dependency tree
	- **ABS** (Naive Absolute encoding)
	- **REL** (Naive Relative encoding)
	- **POS** (Part of speech tags based encoding)
	- **BRK** (Bracket based encoding)
	- **BRK_2P** (2-PLANAR Bracket encoding)
	- **BRK_4B** (4-BITS Bracket encoding)
	- **BRK_7B** (7-BITS Bracket encoding)
	- **6EC** (Hexa-tagging)

Also, for bracket encoding in dependency trees can split the tree in two planes using two different algorithms:

- **GREED**: Greedy algorithm for planar separation.
- **PROP**: Propagation algorithm for planar separation.

## Usage

Can be used to encode single files with encode_const.py or encode_deps.py respectively or decode single files with decode_const.py or decode_deps.py

The parameters available for CoDeLin are:
- Formalism: Indicates the formalism in which input data is. Values = [CONST | DEPS].
- Operation: Indicates if we want to turn trees into labels or labels into trees. Values = [ENC | DEC].
- Encoding: Indicates the encoding type that we want to use to encode/decode the input data; Values = [ABS, REL, DYN, GAP, 4EC, JUX, POS, BRK, BRK_2P, BRK_4B, BRK_7B, 6EC].
- Input file: Path of the input file to encode/decode; Value: string.
- Ouptut file: Path to save the decoded/encoded file; Value: string.
- Separator: Character or String used to separate the different fields of the encoded labels; Indicated by: --sep string.
- Part of Speech tags: Flag that if present the system will employ a part-of-speech tagging library to add POS tags to the decoded trees. By default this is not enabled. Indicated by the flag --postags.
- POS Language: Field indicating the language to use during part of speech tagging. By default is English. Indicated by --lang language_code.
- Features: Field indicating an array of features to extract during the encoding process from the source treebank and add them to the .labels output file. If certain feature does not exist for a word, by default the system will set a '_' character. Indicated by --feats feat_1, feat_2, feat_3...
- Time: Flag indicating if we should output time information
- Multitask: Flag indicating if the output format should have each field of the label as a separate column to allow for multi-task training.

Constituent only parameters:
- Joiner: Character or String used to join the unary chains in the labels; Indicated by: --joiner string.
- Conflict: Node label conflict resolution strategy to apply during the decoding of constituent trees. The available options are take the first label, take the last or take the most repeated; Indicated by --conflict [strat_first | strat_last | start max]. Default is start_max.
- Allow nulls: Flag that if present will allow nulls in the decoded constituent tree. Indicated by --nulls.
- Incremental: Flag that if present will encode the constituent trees in an incremental fashion. Only available for absolute, relative and dynamic encoding. Indicated by --incremental.
- Binary: Flag that if present will turn the constituent tree into a binarized version (i.e. adding non terminal dummy nodes). Only available for absolute, relative and dynamic encoding (as tetratagging and gaps encodings already need the tree to be in binary form). Indicated by --binary flag.
- Binary Direction: Direction to follow during the tree binarization algorithm. It corresponds with right-branch or left-branch binarization. Indicated by --b_direction [L | R]
- Binary Marker: Character or characters added to the artificial intermediate non-terminal nodes. Indicated by --b_marker string. 
- Traverse: Traversal order for tetratagging encoding. Indicated by --traverse [preorder | postorder | inorder]
- Gaps Mode: Open or closed gaps for the gaps encoding. Indicated by --gap_mode [open | close]

Dependency only parameters:
- Displacement: Flag indicating to use displacement in bracket based encodings (i.e. encode the label of word w_i in l_i+1); Indicated by the flag --disp.
- Planar algorithm: Algorithm employed in 2-planar bracket based encoding; Indicated by: --planar [GREED | PROPAGATE].
- Single root: Flag that if present will post-process dependency trees to force root uniqueness. Indicated by --sroot.
- Root search: Indicates the method of root search employed in dependency parsing. The available options are take the first node with head=0 as root or take the first node with rel=0 as root; Indicated by --rsearch [start_gethead | strat_getrel]. Default is strat_gethead.
- Hang from Root: Flag that if present forces encoding of root dependencies in relative encoding as a special label (e.g. encode '-NONE-_root' instead of '-3_root'). Indicated by --hfr flag.


### Encode single file example:
```
$ python main.py CONST ENC ABS test.trees test.labels --time --sep _ --ujoiner + --feats lem ADM ASP AZP BIZ
```
```
$ python main.py DEPS ENC BRK_2P test.labels test.trees --time --sep _ --disp --planar GREED --feats c g m mwehead
```
### Decode single file example:
```
$ python main.py CONST DEC ABS test.labels test_decoded.trees --time --sep _ --ujoiner + --conflict C_STRAT_MAX
```
```
$ python main.py DEPS DEC BRK_2P test.labels test_decoded.conllu --time --sep _ --disp
```

## Output Format

The generated labels from this systems are shaped in columns separated by tabulartor characters where the first column is the input token and the last one is the expected output label. The columns in-between are the indicated features.

| Input_Token   | Features      | Output|
| ------------- |:-------------:| -----:|
| Influential   | NNS           |  4_NP |
| members       | IN            |  3_PP |
| of            | DT            |  2_NP |

If we so desire, we can output the labels in a multi-task ready format

| Input_Token   | Features      | Output_1  | Output_2 |
| ------------- |:-------------:|:---------:|:--------:|
| Influential   | NNS           | 4         | NP       |
| members       | IN            | 3         | PP       |
| of            | DT            | 2         | NP       |

## Usage as library

To use CODELIN as a library for a custom workflow it can be used by cloning the repository inside the project working directory and importing it as

```python
from codelin.models import *
from codelin.encs import * 
from codelin.utils import *
```

## Acknowledgments

This work has received funding by the European Research Council (ERC), under the Horizon Europe research and innovation programme (SALSA, grant agreement No 101100615), ERDF/MICINN-AEI (SCANNER-UDC, PID2020113230RB-C21), Xunta de Galicia (ED431C 2020/11), Grant GAP (PID2022-139308OA-I00) funded by MCIN/AEI/10.13039/501100011033/ and by ERDF “A way of making Europe”, and Centro de Investigación de Galicia “CITIC”, funded by the Xunta de Galicia through the collaboration agreement between the Consellería de Cultura, Educación, Formación Profesional e Universidades and the Galician universities for the reinforcement of the research centres of the Galician University System (CIGUS).
