python main.py DEPS ENC $2 ./$1.conllu ./$1.conllu.labels && 
python main.py DEPS DEC $2 ./$1.conllu.labels ./$1.conllu.dec && 
python ./evalud/conll18_ud_eval.py ./$1.conllu ./$1.conllu.dec