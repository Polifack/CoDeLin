from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_TETRA_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree

import re
import copy


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
        if (len(current_level.children) < 1):
            print("[MERGE ERROR] No children found")
            return tree
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
    def __init__(self, separator, unary_joiner, reverse, binary_direction, binary_marker="*"):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.reverse = reverse
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction

    def __str__(self):
        return "Constituent Tetratagging"
    
    def encode(self, constituent_tree, mode="inorder"):
        nodes = []
        labels = []
        words = []
        postags = []
        unary_chains = []
        non_terminals = []
        features = []
    
        # It is needed to collapse unary before binary
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        
        if self.binary_direction == "R":
            constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
        elif self.binary_direction == "L":
            constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
        else:
            raise Exception("Binary direction not supported")
        
        if mode == "inorder":
            C_Tree.inorder(constituent_tree,  lambda x: nodes.append(x))
        elif mode == "preorder":
            C_Tree.preorder(constituent_tree,  lambda x: nodes.append(x))
        elif mode == "postorder":
            C_Tree.postorder(constituent_tree,  lambda x: nodes.append(x))
        else:
            raise Exception("Mode not supported")
        
        # Extract info from the tree
        last_pos = ""
        for n in nodes:
            label_string = ""

            if n.is_preterminal():
                last_pos = n.label
                continue

            if n.is_terminal():
                # get the parent if the parent is a pos tag
                if n.parent is not None and n.parent.is_preterminal():
                    pn = n.parent
                else:
                    pn = n

                # get the parent if the parent is a unary chain
                if pn.parent is not None and pn.parent.is_unary_chain():
                    pn = pn.parent
                else:
                    pn = pn

                # check if it is a right or left child
                if pn.is_right_child():
                    label_string+="l"
                elif pn.is_left_child() or pn.parent is None:
                    label_string+="r"
                
                if self.unary_joiner in last_pos:
                    uc = self.unary_joiner.join(last_pos.split(self.unary_joiner)[:-1])
                    last_pos = last_pos.split(self.unary_joiner)[-1]
                else:
                    uc = ""

                postag, feats = self.get_features(last_pos)
                
                postags.append(postag)
                unary_chains.append(uc)
                words.append(n.label)
                features.append(feats)
                
                last_pos = ""
            
            else:
                if n.is_right_child():
                    label_string+="L"
                elif n.is_left_child() or n.parent is None:
                    label_string+="R"
                non_terminals.append(n.label)
            labels.append(label_string)
        
        # Merge labels in tuples
        labels_merged = []
        for i in range(0, len(labels), 2):
            if i == len(labels)-1:
                labels_merged.append(labels[i])
            else:
                labels_merged.append(labels[i]+labels[i+1])
        
        # Add a final non terminal if needed
        if len(non_terminals)<len(words):
            non_terminals.append("L")
        
        # Create the labels and linearized tree
        c_labels = []
        for i in range(len(words)):
            l_i = C_Label(labels_merged[i], non_terminals[i], unary_chains[i], C_TETRA_ENCODING, "_", "+")
            c_labels.append(l_i)
        lin_tree = LinearizedTree(words, postags, features, c_labels, None)
        return lin_tree

    def decode(self, linearized_tree):
        stack = []
        buffer = copy.deepcopy(linearized_tree.words)
        tree = None
        for word, postag, feats, label in linearized_tree.iterrows():
            a, t, uc = label.n_commons, label.last_common, label.unary_chain
            a1= a[0]
            
            if a1 == "r":
                leaf = buffer.pop(0)
                terminal_tree = build_unary_chain(leaf, postag, uc, self.unary_joiner)
                stack.append(terminal_tree)
            
            if a1 == "l":
                leaf = buffer.pop(0)
                terminal_tree = build_unary_chain(leaf, postag, uc, self.unary_joiner)
                
                if len(stack)==0:
                    stack.append(terminal_tree)
                else:
                    stack[-1] = combine(stack[-1], terminal_tree)

            
            if len(buffer)==0:
                break
            
            a2 = a[1]
            if a2 == "R":
                tree = C_Tree(t, [stack[-1], C_Tree.empty_tree()])
                
                if len(stack)==0:
                    stack.append(tree)
                else:
                    stack[-1] = tree
                
            if a2 == "L":
                tree = stack.pop()
                tree = C_Tree(t, [tree, C_Tree.empty_tree()])
                
                if len(stack)==0:
                    stack.append(tree)
                else:
                    stack[-1] = combine(stack[-1], tree)
                
        # If there are more than one tree in the stack, combine them   
        final_tree = stack.pop()
        while(len(stack)>=1):
            final_tree = combine(stack.pop(), final_tree)
        
        final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        return final_tree