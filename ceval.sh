python main.py CONST ENC $2 ./$1.trees ./$1.trees.labels && 
python main.py CONST DEC $2 ./$1.trees.labels ./$1.trees.dec && 
./evalb/evalb ./$1.trees ./$1.trees.dec