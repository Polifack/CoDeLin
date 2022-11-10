# encode and decode owls.conllu file with pos based encoding
python main.py DEPS ENC POS ./test/owls.conllu ./test/owls_d_pos.labels
python main.py DEPS DEC POS ./test/owls_d_pos.labels ./test/owls_dec.conllu --postags --lang en

# encode and deocde owls.trees file with dynamic encoding
python main.py CONST ENC DYN ./test/owls.trees ./test/owls_c_dyn.labels
python main.py CONST DEC DYN ./test/owls_c_dyn.labels ./test/owls_dec.trees