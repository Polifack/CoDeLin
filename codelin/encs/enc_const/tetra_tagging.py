from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_TETRA_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree

import re
import copy

def get_child_directions(t):
    # the parent should stop for the last one
    labels = []
    for node in t.children:
        if node.is_terminal():
            label_string = ""

            if node.is_right_child():
                label_string+="l"
            elif node.is_left_child():
                label_string+="r"
            
            if node.parent.is_right_child():
                label_string+="L"
            elif node.parent.is_left_child():
                label_string+="R"
            
            labels.append(label_string)
        child_labels = get_child_directions(node)
        for label in child_labels if child_labels != [] else []:
            labels.append(label)
    
    return labels

def combine(tree, new_child):
    '''
    Replaces a C_NONE_LABEL inside 'tree'
    with new_child
    '''
    # trees should have only 2 child nodes
    if type(new_child) is str:
        new_child = C_Tree(new_child)
    
    current_level = tree
    
    while(not current_level.has_none_child()):
        current_level = current_level.r_child()

    if current_level.children[0].label == C_NONE_LABEL:
        current_level.children[0] = new_child
    elif current_level.children[1].label == C_NONE_LABEL:
        current_level.children[1] = new_child
    return tree

def build_unary_chain(word, postag, unary_chain, unary_joiner):
    if unary_chain:
        unary_chain = unary_chain.split(unary_joiner)
        unary_chain.reverse()
        pos_tree = C_Tree(postag, C_Tree(word))
        for node in unary_chain:
            temp_tree = C_Tree(node, pos_tree)
            pos_tree = temp_tree
    else:
        pos_tree = C_Tree(postag, C_Tree(word))
    return pos_tree

class C_Tetratag(ACEncoding):
    def __init__(self, separator, unary_joiner, reverse):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.reverse = reverse

    def __str__(self):
        return "Constituent Tetratagging"

    directions_dir = {"lL":0,"lR":1,"rL":2,"rR":3}

    def encode(self, constituent_tree):        
        lc_tree = LinearizedTree.empty_tree()

        # Compute the Binary Tree and the arrows
        binary_tree = C_Tree.to_binary_right(constituent_tree)
        
        binary_tree_collapsed = binary_tree.collapse_unary()
        binary_tree_collapsed = binary_tree_collapsed.remove_preterminals()
        binary_tree_collapsed = C_Tree(C_ROOT_LABEL, binary_tree_collapsed)
        child_dirs = get_child_directions(binary_tree_collapsed)

        # Compute the number of commons
        leaf_paths = binary_tree.path_to_leaves(collapse_unary=True, unary_joiner="+")
        
        for i in range(0, len(leaf_paths)-1):
            path_a = leaf_paths[i]
            path_b = leaf_paths[i+1]
            
            last_common = ""
            for a,b in zip(path_a, path_b):
                if (a!=b):
                    # Remove the digits and aditional feats in the last common node
                    last_common = re.sub(r'[0-9]+', '', last_common)
                    last_common = last_common.split("##")[0]

                    # Get word and POS tag
                    word = path_a[-1]
                    postag = path_a[-2]
                    
                    # Build the Leaf Unary Chain
                    unary_chain = None
                    leaf_unary_chain = postag.split("+")
                    if len(leaf_unary_chain)>1:
                        unary_list = []
                        for element in leaf_unary_chain[:-1]:
                            unary_list.append(element.split("##")[0])

                        unary_chain ="+".join(unary_list)
                        postag = leaf_unary_chain[len(leaf_unary_chain)-1]
                    
                    # Clean the POS Tag and extract additional features
                    postag_split = postag.split("##")
                    feats = [None]

                    if len(postag_split) > 1:
                        postag = re.sub(r'[0-9]+', '', postag_split[0])
                        feats = postag_split[1].split("|")
                    else:
                        postag = re.sub(r'[0-9]+', '', postag)

                    direction = child_dirs[i]
                    c_label = C_Label(direction, last_common, unary_chain, C_TETRA_ENCODING, "_", "+")
                    
                    # Append the data
                    lc_tree.add_row(word, postag, feats, c_label)
                
                    break            
                last_common = a
            
        # n = max number of features of the tree
        lc_tree.n = max([len(f) for f in lc_tree.additional_feats])
        return lc_tree

    def decode(self, linearized_tree):
        stack = []
        buffer = copy.deepcopy(linearized_tree.words)
        tree = None
        for word, postag, feats, label in linearized_tree.iterrows():
            a, t, uc = label.n_commons, label.last_common, label.unary_chain
            a1, a2 = a[0], a[1]
            if a1 == "r":
                leaf = buffer.pop(0)
                terminal_tree = build_unary_chain(leaf, postag, uc, "+")
                stack.append(terminal_tree)
            
            if a1 == "l":
                leaf = buffer.pop(0)
                terminal_tree = build_unary_chain(leaf, postag, uc, "+")
                stack[-1] = combine(stack[-1], terminal_tree)
            
            if len(buffer)==0:
                break

            if a2 == "R":
                tree = C_Tree(t, [stack[-1], C_Tree.empty_tree()])
                stack[-1] = tree
                
            if a2 == "L":
                tree = stack.pop()
                tree = C_Tree(t, [tree, C_Tree.empty_tree()])
                stack[-1] = combine(stack[-1], tree)

        final_tree = stack[0]
        final_tree = C_Tree.restore_from_binary(final_tree)
        return final_tree