from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_TETRA_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree

import re
import copy


def shift_action(node):
    '''
    For SHIFT actions, we encode whether the
    node being shifted is a left or a right child of
    its parent.
    '''
    lbl = "r" if node.is_left_child() else "l"
    return lbl

def reduce_action(node):
    '''
    For REDUCE actions, we encode the identity
    of the non-terminal being reduced as well as
    whether it is a left or a right child
    '''
    lbl =  "R" if node.is_left_child() else "L"
    lc =  node.label
    return lbl, lc

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

## Inorder functions
def encode_inorder(tree, sep, ujoiner):    
    tags    = [n.label for n in tree.get_preterminals()]
    words   = [n.label for n in tree.get_terminals()]

    tree = tree.remove_preterminals()
    nodes = []
    
    
    C_Tree.inorder(tree, lambda x: nodes.append(x))
    lintree = LinearizedTree.empty_tree()
    cl = []
    i = 0
    for node in nodes:
        if node.is_terminal():
            lbl = shift_action(node)
            cl.append(lbl)
        else:
            lbl, lc = reduce_action(node)
            cl.append(lbl)
            
            ### INORDER => Append in non-terminals
            w_i = words[i]
            p_i = tags[i]
            
            # p_i = extract feats
            nc_i = "".join(cl)
            lc_i = lc
            uc_i = None

            # p_i = extract unary 
            if ujoiner in p_i:
                uc_i = ujoiner.join(p_i.split(ujoiner)[:-1])
                p_i = p_i.split(ujoiner)[-1]

            lbl = C_Label(nc=nc_i, lc=lc_i, uc=uc_i, et=C_TETRA_ENCODING, sp=sep, uj=ujoiner)
            lintree.add_row(w_i, p_i, None, lbl)

            i += 1
            cl = []

    # last reduce action
    w_i = words[i]
    p_i = tags[i]
    
    # p_i = extract feats
    nc_i = "".join(cl)
    lc_i = lc if 'lc' in locals() else None
    uc_i = None

    # p_i = extract unary 
    if ujoiner in p_i:
        uc_i = ujoiner.join(p_i.split(ujoiner)[:-1])
        p_i = p_i.split(ujoiner)[-1]
    lbl = C_Label(nc=nc_i, lc=lc_i, uc=uc_i, et=C_TETRA_ENCODING, sp=sep, uj=ujoiner)
    lintree.add_row(w_i, p_i, None, lbl)

    return lintree
def decode_inorder(l_in, ujoiner):
    stack = []
    for word, postag, feats, label in l_in.iterrows():
        operators = list(label.n_commons)
        for op in operators:
            if op == 'r':
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                stack.append(terminal_tree)
            
            elif op == 'l':
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])

                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                if len(stack)==0:
                    stack.append(terminal_tree)
                else:                          
                    stack[-1] = combine(stack[-1], terminal_tree)

            elif op.startswith("R"):
                nt = label.last_common
                tree = C_Tree(nt, [stack[-1], C_Tree.empty_tree()])
                
                if len(stack)==0:
                    stack.append(tree)
                else:
                    stack[-1] = tree

            elif op.startswith("L"):
                nt = label.last_common
                tree = stack.pop()
                tree = C_Tree(nt, [tree, C_Tree.empty_tree()])
                
                if len(stack)==0:
                    stack.append(tree)
                else:
                    stack[-1] = combine(stack[-1], tree)

    final_tree = stack.pop()
    return final_tree

## Preorder functions

def encode_preorder(tree, sep, ujoiner):
    tags    = [n.label for n in tree.get_preterminals()]
    words   = [n.label for n in tree.get_terminals()]

    tree = tree.remove_preterminals()
    nodes = []
    
    C_Tree.preorder(tree, lambda x: nodes.append(x))
    lintree = LinearizedTree.empty_tree()
    cl = []
    lc = None
    i = 0
    for node in nodes:
        if node.is_terminal():
            lbl = shift_action(node)
            cl.append(lbl)
            
            ### PREORDER => Append in terminals
            w_i = words[i]
            p_i = tags[i]
            
            # p_i = extract feats
            nc_i = "".join(cl)
            lc_i = lc
            uc_i = None

            # p_i = extract unary 
            if ujoiner in p_i:
                uc_i = ujoiner.join(p_i.split(ujoiner)[:-1])
                p_i = p_i.split(ujoiner)[-1]

            # fix last reduce action
            if lc_i is None:
                lc_i = C_NONE_LABEL
            
            lbl = C_Label(nc=nc_i, lc=lc_i, uc=uc_i, et=C_TETRA_ENCODING, sp=sep, uj=ujoiner)
            lintree.add_row(w_i, p_i, None, lbl)

            i += 1
            lc = None
            cl = []
        else:
            lbl, lc_i = reduce_action(node)
            if lc is None:
                lc = lc_i
            else:
                lc = lc + ">" + lc_i
            cl.append(lbl)
    
    return lintree
def decode_preorder(l_in, ujoiner):
    stack = []
    for word, postag, feats, label in l_in.iterrows():
        operators = list(label.n_commons)
        for op in operators:
            if op == 'r':
                # r => node is a left terminal children, add it to the stack
                
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                if len(stack) == 0:
                    # single-word sentence
                    stack.append(terminal_tree)
                    continue
                

                stack[-1].children[0] = terminal_tree
            
            elif op == 'l':
                # l => node is a right terminal child, combine it with the top of the stack

                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                parent_tree = stack.pop()
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                parent_tree.children[1] = terminal_tree

                while not parent_tree.has_none_child() and len(stack)>0:
                    parent_tree = stack.pop()
                    parent_tree.update_custody()
                
                stack.append(parent_tree)

            elif op.startswith("R"):
                # R => node is a left non terminal child, combine it with the top of the stack
                
                # get the non terminal (or non terminals)
                if ">" in label.last_common:
                    nt = label.last_common.split(">")[0]
                    label.last_common = ">".join(label.last_common.split(">")[1:])
                else:
                    nt = label.last_common
                
                if len(stack) > 0:
                    l_child = C_Tree(nt, children=[C_Tree(C_NONE_LABEL), C_Tree(C_NONE_LABEL)])
                    stack[-1].children[0] = l_child
                    stack[-1].update_custody()
                    
                    stack.append(l_child)
                else:
                    stack.append(C_Tree(nt, [C_Tree.empty_tree(), C_Tree.empty_tree()]))

            elif op.startswith("L"):
                # L => node is a right non terminal child, combine it with the top of the stack
                
                # get the non terminal (or non terminals)
                if ">" in label.last_common:
                    nt = label.last_common.split(">")[0]
                    label.last_common = ">".join(label.last_common.split(">")[1:])
                else:
                    
                    nt = label.last_common
                
                if len(stack)>0:
                    r_child = C_Tree(nt, [C_Tree.empty_tree(), C_Tree.empty_tree()])
                    stack[-1].children[1] = r_child
                    stack[-1].update_custody()
                
                    stack.append(r_child)
                else:
                    stack.append(C_Tree(nt, [C_Tree.empty_tree(), C_Tree.empty_tree()]))
                    
    final_tree = stack.pop()
    return final_tree

## Postorder functions

def encode_postorder(tree, sep, ujoiner):
    tags    = [n.label for n in tree.get_preterminals()]
    words   = [n.label for n in tree.get_terminals()]

    tree = tree.remove_preterminals()
    nodes = []
    
    C_Tree.postorder(tree, lambda x: nodes.append(x))
    lintree = LinearizedTree.empty_tree()
    cl = []
    lc = None
    i = 0
    for node in nodes:
        if node.is_terminal():
            lbl = shift_action(node)
            cl.append(lbl)
            
            ### POSTORDER  => Append in terminals (but binarized to the left)
            w_i = words[i]
            p_i = tags[i]
            
            # p_i = extract feats
            nc_i = "".join(cl)
            lc_i = lc
            uc_i = None

            # p_i = extract unary 
            if ujoiner in p_i:
                uc_i = ujoiner.join(p_i.split(ujoiner)[:-1])
                p_i = p_i.split(ujoiner)[-1]

            if lc_i is None:
                lc_i = C_NONE_LABEL
            
            lbl = C_Label(nc=nc_i, lc=lc_i, uc=uc_i, et=C_TETRA_ENCODING, sp=sep, uj=ujoiner)
            lintree.add_row(w_i, p_i, None, lbl)
            i += 1

            
            lc = None
            cl = []
        else:
            lbl, lc_i = reduce_action(node)
            if lc is None:
                lc = lc_i
            else:
                lc = lc + ">" + lc_i
            cl.append(lbl)
    
    
    # last non-terminal node (postorder will end in a non-terminal node)
    nc_i = "".join(cl)
    lintree.labels[-1].n_commons += nc_i
    lintree.labels[-1].last_common+=">"+lc if lc is not None else ""
    return lintree
def decode_postorder(l_in, ujoiner):
    stack = []
    for word, postag, feats, label in l_in.iterrows():
        operators = list(label.n_commons)
        for op in operators:
            if op == 'r':
                # build terminal tree
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                # r => insert the node in the stack
                stack.append(terminal_tree)
            
            elif op == 'l':
                # build terminal tree
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])

                # remove from the non-terminal list the associate -none- (if exists)
                if C_NONE_LABEL == label.last_common.split(">")[0]:
                    label.last_common = ">".join(label.last_common.split(">")[1:])

                # See if we can close this node
                if not stack[-1].has_none_child():
                    stack.append(terminal_tree)    
                    continue
                else:
                    parent_tree = stack.pop()
                    parent_tree.children[1] = terminal_tree

                # moving up the tree until we find a node with a right child
                while not parent_tree.has_none_child() and len(stack)>0:
                    parent_tree = stack.pop()
                    parent_tree.update_custody()
                
                stack.append(parent_tree)

            elif op.startswith("R"):
                # get the non terminal
                if ">" in label.last_common:
                    nt = label.last_common.split(">")[0]
                    label.last_common = ">".join(label.last_common.split(">")[1:])
                else:
                    nt = label.last_common

                # node is a left non terminal child, combine it with the top of the stack
                if len(stack)>0:
                    r_child = stack.pop()
                    l_child = stack.pop()
                    p_tree  = C_Tree(nt, children=[l_child, r_child])
                    p_tree.update_custody()
                    
                    stack.append(p_tree)
                else:
                    stack.append(C_Tree(nt, [C_Tree.empty_tree(), C_Tree.empty_tree()]))

            elif op.startswith("L"):
                # L => node is a right non terminal child, combine it with the top of the stack
                
                # get the non terminal (or non terminals)
                if ">" in label.last_common:
                    nt = label.last_common.split(">")[0]
                    label.last_common = ">".join(label.last_common.split(">")[1:])
                else:
                    nt = label.last_common

                if len(stack)>0:
                    r_child = stack.pop()
                    l_child = stack.pop()
                    p_tree  = C_Tree(nt, children=[l_child, r_child])
                    p_tree.update_custody()

                    stack.append(p_tree)

    final_tree = stack.pop()
    return final_tree

class C_Tetratag(ACEncoding):
    def __init__(self, separator, unary_joiner, mode, binary_marker="*"):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.mode = mode
        self.binary_marker = binary_marker

    def __str__(self):
        return "Constituent Tetratagging"
    
    def encode(self, constituent_tree):
    
        # It is needed to collapse unary before binary
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        
        if self.mode == "inorder":
            # Inorder must be linearized to the right
            constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
            return encode_inorder(constituent_tree, self.separator, self.unary_joiner)
        elif self.mode == "preorder":
            # Preorder must be linearized to the right
            constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
            return encode_preorder(constituent_tree, self.separator, self.unary_joiner)
        elif self.mode == "postorder":
            # Postorder must be linearized to the left
            constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
            return encode_postorder(constituent_tree, self.separator, self.unary_joiner)
        else:
            raise Exception("Mode not supported")

    def decode(self, linearized_tree):
        if self.mode == "inorder":
            final_tree = decode_inorder(linearized_tree, self.unary_joiner)
        elif self.mode == "preorder":
            final_tree = decode_preorder(linearized_tree, self.unary_joiner)
        elif self.mode == "postorder":
            final_tree = decode_postorder(linearized_tree, self.unary_joiner)

        C_Tree.restore_from_binary(final_tree, binary_marker=self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        return final_tree