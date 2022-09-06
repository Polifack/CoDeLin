# encode and decode owls.conllu file with pos based encoding
python main.py DEPS ENC POS owls.conllu owls_d_pos.labels
python main.py DEPS DEC POS owls_d_pos.labels owls_dec.conllu --postags --lang en

# encode and deocde owls.trees file with dynamic encoding
python main.py CONST ENC DYN owls.trees owls_c_dyn.labels
python main.py CONST DEC DYN owls_c_dyn.labels owls_dec.trees