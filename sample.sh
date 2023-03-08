### DEPENDENCY TREE ENCODING ###

# encode and decode owls.conllu file with absolute encoding
python main.py DEPS ENC ABS ./test/owls.conllu ./test/owls.conllu.abs.labels
python main.py DEPS DEC ABS ./test/owls.conllu.abs.labels ./test/owls.dec.abs.conllu

# encode and decode owls.conllu file with relative encoding
python main.py DEPS ENC REL ./test/owls.conllu ./test/owls.conllu.rel.labels
python main.py DEPS DEC REL ./test/owls.conllu.rel.labels ./test/owls.dec.rel.conllu

# encode and decode owls.conllu file with pos based encoding
python main.py DEPS ENC POS ./test/owls.conllu ./test/owls.conllu.pos.labels
python main.py DEPS DEC POS ./test/owls.conllu.pos.labels ./test/owls.dec.pos.conllu

# encode and decode owls.conllu file with bracket based encoding
python main.py DEPS ENC BRK_2P ./test/owls.conllu ./test/owls.conllu.brk.labels
python main.py DEPS DEC BRK_2P ./test/owls.conllu.brk.labels ./test/owls.dec.brk.conllu

### CONSTITUENCY TREE ENCODING ###

# encode and decode owls.tree file using absolute encoding
python main.py CONST ENC ABS ./test/owls.trees ./test/owls.trees.abs.labels
python main.py CONST DEC ABS ./test/owls.trees.abs.labels ./test/owls.dec.abs.trees

# encode and decode owls.tree file using relative encoding
python main.py CONST ENC REL ./test/owls.trees ./test/owls.trees.rel.labels
python main.py CONST DEC REL ./test/owls.trees.rel.labels ./test/owls.dec.rel.trees

# encode and deocde owls.trees file with dynamic encoding
python main.py CONST ENC DYN ./test/owls.trees ./test/owls.trees.dyn.labels
python main.py CONST DEC DYN ./test/owls.trees.dyn.labels ./test/owls.dec.dyn.trees

# encode and deocde owls.trees file with incremental encoding
python main.py CONST ENC INC ./test/owls.trees ./test/owls.trees.incr.labels
python main.py CONST DEC INC ./test/owls.trees.incr.labels ./test/owls.dec.incr.trees
