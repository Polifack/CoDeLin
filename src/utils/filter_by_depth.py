import argparse
from stanza.models.constituency.tree_reader import read_tree_file
from stanza.models.constituency.parse_tree import Tree
from conllu import parse_tree_incr

'''
Python script that splits a treebank into different files
by the depth of the trees inside that file
'''

def filter_by_depth(in_path):
    trees=read_tree_file(in_path)
    filtered_trees={}
    for tree in trees:
        tree_depth = tree.depth()
        if tree_depth not in filtered_trees.keys():
            filtered_trees[tree_depth] = []
        filtered_trees[tree_depth].append(tree)
    return filtered_trees



parser = argparse.ArgumentParser(description='Prints all features in a constituent treebank')
parser.add_argument('input', metavar='in file', type=str, help='Path of the file to filter')
parser.add_argument('output', metavar='in file', type=str, help='Path of the output files')
parser.add_argument('--range', metavar='range', type=int, help='Range of levels', required=False, default=3)
args = parser.parse_args()

filtered_trees = filter_by_depth(args.input)

ts={}
depth_list = list(filtered_trees.keys())
depth_list.sort()
print(depth_list)
for i in range(0, len(depth_list)-1, args.range):
    starting_depth = depth_list[i]
    print(starting_depth)
    
    cts = []
    for j in range(0,(args.range)):
        if (i+j)<len(depth_list)-1:
            print("--",depth_list[i+j])
            current_depth = depth_list[i+j]
            cts.extend(filtered_trees[current_depth])

    setname = str(starting_depth)+"-"+str(current_depth)
    ts[setname]=cts

for dr in ts:
    cts = ts[dr]
    print(cts)
    Tree.write_treebank(cts, args.output+"_"+dr+".trees")
