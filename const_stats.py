import json
import argparse
from codelin.models.const_tree import C_Tree
from codelin.encs.enc_const import *
from codelin.utils.constants import *

'''
File to extract data from constituent files
'''

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Extractor of stats for constituent treebanks')
    parser.add_argument('--files', metavar='FILE', type=str, nargs='+',
                    help='a list of input files')

    args = parser.parse_args()

    for file in args.files:
        file = open(file, 'r')
        d = []
        w = []
        bl = []
        br = []
        bf = []
        for t in [C_Tree.from_string(line) for line in file.readlines()]:
            d.append(t.depth())
            w.append(max(t.width().values()))
            
            t = t.collapse_unary("+")
            t = t.remove_preterminals()
            
            bf.append(t.average_branching_factor())
            branching = t.branching()
            branching_left = branching["L"]/(branching["L"]+branching["R"])*100 if branching["L"]+branching["R"]!=0 else 0
            branching_right = branching["R"]/(branching["L"]+branching["R"])*100 if branching["L"]+branching["R"]!=0 else 0
            bl.append(branching_left)
            br.append(branching_right)
    
    print("Average depth =",sum([x for x in d])/len(d))
    print("Average max width =",sum([x for x in w])/len(w))
    print("Average branching factor =",sum([x for x in bf])/len(bf))
    print("Average left branching =",sum([x for x in bl])/len(bl),"%")
    print("Average right branching =",sum([x for x in br])/len(br),"%")