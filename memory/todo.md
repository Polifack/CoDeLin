## BACKLOG:

[x] Implement tetra-tagging.
[x] Implement binarization for all constituent encodings.
[x] Implement incremental encodings.
[x] Evaluate incremental and binary encodings in PTB.
	!! The binary encodings were not tested correctly as the part of speech tags contain the collapsed unary chains. Must re-evaluate
[x] Search for NNE datasets
[x] Implement NER 2 Trees
[x] Implement NER 2 BIO/BILOU
[x] Implement postorder and inorder tetratagging. Currently we have only inorder.
[x] Darse de alta en https://altausuarios.cesga.es/
[x] Implement +G,-G encoding: No funciona; se necesitan mas labels


## WIP
[ ] Huggingface para los modelos de lenguaje con NER // meter multi-task a los modelos https://huggingface.co/docs/transformers/tasks/token_classification
[ ] Implement gaps encoding with n labels (e.g. instead of encoding '-G' for all gaps encode -G1, -G2...?)
[ ] Implement decoding heuristics for tree2ner 
	- NER trees must have only one root node
	- Check all open entities are closed
	- Check max entity length
[ ] Find evaluation script for NER:
	- Evaluate by checking complete entities
	- Evaluate by checking correct ner tokens


## TODO

[ ] Get stats of ner trees (e.g. average-depth, number of trees with depth higher than n...)
[ ] Train the BIO and BILOU models for GENIA
[ ] Evaluate all models of NER
[ ] Discontinous Parsing Implementation for Discontinuous NER
[ ] Multi task learning with several encodings
[ ] Multi output model with several encodings (e.g. output relative + absolute and use them both to get a better decoding)
[ ] Multi task learning with NER (parse tree + ner tree)

[ ] Attach juxtaposed transition based constituent parsing (as much transitions as words?) [link](https://arxiv.org/pdf/2010.14568.pdf)
[ ] Train with PTB / SPMRL for all encodings. Test with BILSTM. Use ROBERTA. Do it with huggingface.

[ ] Voting con several encodings?
[ ] Quantified models? What is faster lstm or quantified transformers?
[ ] XML-Roberta quantified?

## Deadlines
- AACL  23/05
- EMNLP 23/06
