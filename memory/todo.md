## BACKLOG:

[x] => Implement tetra-tagging.
[x] => Implement binarization for all constituent encodings.
[x] => Implement incremental encodings.
[x] => Evaluate incremental and binary encodings in PTB.
	!! The binary encodings were not tested correctly as the part of speech tags contain the collapsed unary chains. Must re-evaluate
[x] => Search for NNE datasets
[x] => Implement NER 2 Trees
[x] => Implement NER 2 BIO/BILOU
[x] => Implement postorder and inorder tetratagging. Currently we have only inorder.

## TODO

[ ] => Get stats of ner trees (e.g. average-depth, number of trees with depth higher than n...)
[ ] => Implement decoding heuristics for tree2ner (e.g. only one root)
[ ] => Train the BIO and BILOU models for GENIA
[ ] => Find evaluation script for NER
[ ] => Evaluate all models of NER
[ ] => Discontinous Parsing Implementation for Discontinuous NER
[ ] => Multi task learning with several encodings
[ ] => Multi output model with several encodings (e.g. output relative + absolute and use them both to get a better decoding)
[ ] => Multi task learning with NER (parse tree + ner tree)

## MISC
[ ] => Get number of trees that can currently be encoded and get the ones that cant
[ ] => Implement +G,-G encoding
[ ] => Is there a relation between Tetratagging and Relative Encoding?
	
	- There are several cases of relative labels with the same value and different 'arrows' assignment (e.g. -1=rL and -1=lL)
	- Decoding does not work with 3 labels 
	- Decoding does not work with 4 labels (see inconsistencies from picture)

[ ] huggingface para los modelos de lenguaje con NER // meter multi-task a los modelos https://huggingface.co/docs/transformers/tasks/token_classification
[ ] darse de alta en https://altausuarios.cesga.es/
[ ] Would it work with n labels? (e.g. instead of encoding '-G' for all gaps encode -G1, -G2...?)
