from src.utils.constants import C_END_LABEL, C_NONE_LABEL

from stanza.models.constituency.parse_tree import Tree

import copy

'''
    File with auxiliary functions useful to tree parsing in 
    constituent parsing encodings
'''

def collapse_unary(tree, unary_joiner):
    '''
    Function that collapses unary chains
    into single nodes using a unary_joiner as join character
    '''
    for child in tree.children:
        collapse_unary(child, unary_joiner)
    if len(tree.children)==1 and not tree.is_preterminal():
        tree.label += unary_joiner + tree.children[0].label
        tree.children = tree.children[0].children

def add_end_node(tree):
    '''
    Function that adds a dummy end node to the tree
    to ease parsing tasks
    '''
    tree.children = (*tree.children, Tree(C_END_LABEL,[Tree(C_END_LABEL)]))

def path_to_leaves(tree):
    '''
    Function that given a Tree returns a list of paths
    from the root to the leaves, encoding a level index into
    nodes to make them unique.
    '''
    return path_to_leaves_rec(tree,[],[],0)
def path_to_leaves_rec(node, current_path, paths, idx):
    if (len(node.children)==0):
        current_path.append(node.label)
        paths.append(current_path)
    else:
        common_path = copy.deepcopy(current_path)
        common_path.append(node.label+str(idx))
        for child in node.children:
            path_to_leaves_rec(child, common_path, paths, idx)
            idx+=1
    return paths

def fill_pos_nodes(current_level, postag, word, unary_chain, unary_joiner):
    '''
    Inserts a preterminal Part of Speech node with a leaf Word node
    in the selected level of the tree. If indicated, also sets the
    corresponding Leaf Unary Chain before the POS node.
    '''
    # Build the Unary Tree
    if unary_chain:
        unary_chain = unary_chain.split(unary_joiner)
        unary_chain.reverse()
        pos_tree = Tree(postag, Tree(word))
        for node in unary_chain:
            temp_tree=Tree(node, pos_tree)
            pos_tree=temp_tree
    else:
        pos_tree=Tree(postag, Tree(word))

    # if current level has no children
    if current_level.children == [C_NONE_LABEL]:
        current_level.children=[pos_tree]
    else:
        current_level.children=(*current_level.children,pos_tree)