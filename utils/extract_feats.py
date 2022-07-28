import argparse
from stanza.models.constituency.tree_reader import read_tree_file
from conllu import parse_tree_incr
from models.dependency import ConllNode

def extract_features_const(in_path):
    trees=read_tree_file(in_path)
    feats_list=set()
    for tree in trees:
        postags = tree.yield_preterminals()
        
        for postag in postags:
            if len(postag.label.split("##"))<=1:
                continue

            feats = postag.label.split("##")[1].split("|")
            for feat in feats:
                fs = feat.split("=")
                if len(fs)>1:
                    key=fs[0]
                    feats_list.add(key)

    
    return sorted(feats_list)

def extract_features_conll(in_path):
    feats_list=set()
    i=0
    for tree in parse_tree_incr(open(in_path)):
        data = tree.serialize().split('\n')
        for line in data:
            # check if not valid line
            if (len(line)<=1) or len(line.split('\t'))<10 or line[0] == "#":
                continue

            conll_node = ConllNode.from_string(line)
            feats = conll_node.feats.split("|")
            for feat in feats:
                fs = feat.split("=")
                if len(fs)>1:
                    key=fs[0]
                    feats_list.add(key)

    return sorted(feats_list)
    

'''
Python script that returns a ordered list of the features
included in a conll tree or a constituent tree
'''

parser = argparse.ArgumentParser(description='Prints all features in a constituent treebank')
parser.add_argument('form', metavar='formalism', type=str, choices=['CONST','DEPS'], help='Grammar encoding the file to extract features')
parser.add_argument('input', metavar='in file', type=str, help='Path of the file to clean (.trees file).')
args = parser.parse_args()
if args.form=='CONST':
    feats = extract_features_const(args.input)
elif args.form=='DEPS':
    feats = extract_features_conll(args.input)
print(" ".join(feats))