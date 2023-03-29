import json
import argparse
from codelin.models.const_tree import C_Tree
from codelin.encs.enc_const import *
from codelin.utils.constants import *


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='CoDeLin Ner to Trees')
    parser.add_argument('input', metavar='in file', type=str,help='Input NER file')
    

    args = parser.parse_args()
    
    f = open(args.input, 'r')


    max_depth = 0
    max_depth_tree = None
    for line in f.readlines():
        tree = C_Tree.from_string(line)
        max_depth = tree.depth() if tree.depth() > max_depth else max_depth
        max_depth_tree = tree if tree.depth() == max_depth else max_depth_tree
    
    print(max_depth)
    print(max_depth_tree)