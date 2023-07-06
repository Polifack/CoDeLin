import os

treebanks_path = "./Treebanks/bf"
for folder in os.listdir(treebanks_path):
    treebank_path = os.path.join(treebanks_path, folder)

    train_file = [file for file in os.listdir(treebank_path) if ('train' in file) and ('.conllu' in file)][0]
    train_file = os.path.join(treebank_path, train_file)

    dev_file = [file for file in os.listdir(treebank_path) if ('dev' in file) and ('.conllu' in file)][0]
    dev_file = os.path.join(treebank_path, dev_file)

    test_file = [file for file in os.listdir(treebank_path) if ('test' in file) and ('.conllu' in file)][0]
    test_file = os.path.join(treebank_path, test_file)

    output_file = os.path.join(treebank_path, "pred.conllu")
    

    # python -m supar.cmds.dep.biaffine train -b -d 0 -c dep-biaffine-en -p model -f char --embed giga-100 --bert xlm-roberta --train ~/Treebanks/20ag/PTB/ptb-train.conllu --dev ~/Treebanks/20ag/PTB/ptb-dev.conllu --test ~/Treebanks/20ag/PTB/ptb-test.conllu 
    command = "python -m supar.cmds.dep.biaffine train -b -d 0 -c dep-biaffine-en -p model -f char --embed giga-100 --bert xlm-roberta --train " + train_file + " --dev " + dev_file + " --test " + test_file + " --data " + test_file + " --pred " + output_file
    print("[*]",command)
    os.system(command)
