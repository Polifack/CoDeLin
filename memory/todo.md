## BACKLOG:

[x] Implement tetra-tagging.
[x] Implement binarization for all constituent encodings.
[x] Implement incremental for all constituent encodings.
[x] Evaluate incremental and binary encodings in PTB.
[x] Search for NNE datasets
[x] Implement NER 2 Trees
[x] Implement NER 2 BIO/BILOU
[x] Implement postorder and inorder tetratagging. Currently we have only inorder.
[x] Sign up en https://altausuarios.cesga.es/
[x] Implement +G,-G encoding: No funciona; se necesitan mas labels
[x] Implement gaps encoding with n labels (e.g. instead of encoding '-G' for all gaps encode -G1, -G2...?)
[x] Attach juxtaposed transition based constituent parsing (as much transitions as words?) [link](https://arxiv.org/pdf/2010.14568.pdf)
[x] Develop multi task learning system for several encodings
[x] Check the gaps encoding with both binary directions and reverse
[x] Check the tetratag with several orders with both binary directions and reverse
[x] Check the juxtaposed encoding with reverse and binarization
[x] Implement a better constituent stats extraction


## WIP

[ ] Train with PTB / SPMRL for all encodings. Test with BILSTM. Use ROBERTA.

## TODO

[ ] Get stats of NER trees (e.g. average-depth, number of trees with depth higher than n...)

[ ] Train the BIO and BILOU models for GENIA

[ ] Evaluate all models of NER

[ ] Discontinous Parsing Implementation

[ ] Implement decoding heuristics for tree2ner 
	=> NER trees must have only one root node
	=> Check all open entities are closed
	=> Check max entity length

[ ] Find evaluation script for NER:
	=> Evaluate by checking complete entities
	=> Evaluate by checking correct ner tokens

[ ] Take advantage of the MTL system to get a encoding with several outputs and use them both to get a better decoding
	=> For example, tetra + relative + gaps

[ ] Multi task learning with NER (parse tree + ner tree)

[ ] Multi task learning with sentiment analysis (parse tree + sentiment indicator)
	=> We could use the Stanford sentiment treebank

[ ] Check SPMRL treebanks branching factor
	=> We could compute the branching factor by counting the number of parenthesis together in the treebank
		
		(A (B C)) vs ((A B) C)
		=======================
		right_br  vs  left_br

[ ] Check semantic dependency parsing
		=> We could employ the planar encoding for this task (instead of *only* one outgoing arc, we could have several arcs)
		=> biaffine attention? (https://arxiv.org/pdf/1611.01734.pdf)

[ ] Abstract meaning representation (AMR) parsing
		=> We could employ a seq2seq model to turn words into concepts
		=> We could employ Sequence Labeling after that

[ ] Once the models are trained, extract stats per tree depth (e.g. f1 score for trees with depth<=3)

[ ] Check for models quantification in the MTL setup

[ ] Write Introduction and State of the art for paper

[ ] Profundidad arbol // Tam arbol y numero etiquetas (e.g. filtrar por 3, por 4...)

[ ] Etiquetas en multi-task (dividiendo los campos de etiqueta)

## Deadlines
- AACL  23/05
- EMNLP 23/06
