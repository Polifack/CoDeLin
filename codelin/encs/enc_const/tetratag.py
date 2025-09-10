from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_TETRA_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree
from typing import List

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
            current_level.children.append(new_child)
            return tree
            
        current_level = current_level.r_child()
    
    # problem if here it does not have a none label
    if len(current_level.children)==1:
        current_level.children.append(new_child)
        return tree


    if current_level.children[0].label == C_NONE_LABEL:
        current_level.children[0] = new_child
    
    elif current_level.children[1].label == C_NONE_LABEL:
        current_level.children[1] = new_child
    
    return tree

## Inorder functions
def encode_inorder(tree: C_Tree, sep, ujoiner):    
    tags    = [n.label for n in tree.get_preterminals()]
    words   = [n.label for n in tree.get_terminals()]
    tree = tree.remove_preterminals()
    nodes: List[C_Tree] = []

    
    C_Tree.inorder(tree, lambda x: nodes.append(x))
    lintree = LinearizedTree.empty_tree()
    cl = []
    lc = None
    i = 0

    for node in nodes:
        if node.is_terminal():
            # print(f"[DEBUG] processing node {node.label} and it is a right child {node.is_right_child()}")
            lbl = shift_action(node)
            cl.append(lbl)
        else:
            lbl, lc = reduce_action(node)
            cl.append(lbl)
            
            ### INORDER => Append in non-terminals
            # print(f"processing node {node.label} and trying to access word {i}")
            w_i = words[i]
            p_i = tags[i] if i < len(tags) else "POS"
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
            i+=1
            cl = []
    
    return lintree


def decode_inorder(l_in, ujoiner):
    stack = []
    for word, postag, feats, label in l_in.iterrows():
        # ensure n_commons is a str
        if isinstance(label.n_commons, int):
            label.n_commons = 'l'
        operators = list(label.n_commons)

        for op in operators:

            # --- SHIFT = build a leaf subtree + unary chain, then push (if 'r') or combine (if 'l') ---

            if op == 'r':
                # build leaf
                if postag == C_NONE_LABEL:
                    t = C_Tree(word)
                else:
                    t = C_Tree(postag, [C_Tree(word)])
                
                # unary-chain (e.g. FIRST, NAME, etc)
                if label.unary_chain:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        t = C_Tree(uc, [t])
                stack.append(t)

            elif op == 'l':
                # build leaf
                if postag == C_NONE_LABEL:
                    t = C_Tree(word)
                else:
                    t = C_Tree(postag, [C_Tree(word)])
                if label.unary_chain:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        t = C_Tree(uc, [t])

                # combine into placeholder on top-of-stack (or push if empty)
                if not stack:
                    stack.append(t)
                else:
                    stack[-1] = combine(stack[-1], t)

            # --- REDUCE = build a new NT with one child + ∅ placeholder ---

            elif op.startswith("R"):
                nt = label.last_common
                if not stack:
                    # first operator is R => we must first build the leaf
                    if postag == C_NONE_LABEL:
                        t = C_Tree(word)
                    else:
                        t = C_Tree(postag, [C_Tree(word)])
                    if label.unary_chain:
                        for uc in reversed(label.unary_chain.split(ujoiner)):
                            t = C_Tree(uc, [t])
                    # now wrap
                    tree = C_Tree(nt, [t, C_Tree.empty_tree()])
                    stack.append(tree)
                else:
                    # normal left-corner reduce
                    tree = C_Tree(nt, [stack[-1], C_Tree.empty_tree()])
                    stack[-1] = tree

            elif op.startswith("L"):
                nt = label.last_common
                if not stack:
                    # first operator is L => same hack
                    if postag == C_NONE_LABEL:
                        t = C_Tree(word)
                    else:
                        t = C_Tree(postag, [C_Tree(word)])
                    if label.unary_chain:
                        for uc in reversed(label.unary_chain.split(ujoiner)):
                            t = C_Tree(uc, [t])
                    tree = C_Tree(nt, [t, C_Tree.empty_tree()])
                    stack.append(tree)
                else:
                    # normal right-corner reduce
                    child = stack.pop()
                    tree  = C_Tree(nt, [child, C_Tree.empty_tree()])
                    if stack:
                        stack[-1] = combine(stack[-1], tree)
                    else:
                        stack.append(tree)

    # join up any remaining pieces
    while len(stack) > 1:
        t = stack.pop()
        stack[-1] = combine(stack[-1], t)

    return stack.pop()

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
        # print(word,'\t\t', label)
        operators = list(label.n_commons)
        for op in operators:
            # print("*** running",word,op)
            for x in stack:
                C_Tree.pretty_print(x)
            
            if op == 'r':
                # r => node is a left terminal children, add it to the stack
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])
                
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                # single-word sentence
                if len(stack) == 0:    
                    terminal_tree.children.append(C_Tree.empty_tree())
                    stack.append(terminal_tree)
                    continue
                
                # print(">> running r on", stack[-1])
                stack[-1].children[0] = terminal_tree
            
            elif op == 'l':
                # l => node is a right terminal child, combine it with the top of the stack
                terminal_tree = C_Tree(postag, children=[C_Tree(word)])

                # situation where the first predicted label is a l label
                if len(stack) == 0:
                    terminal_tree.children.append(C_Tree.empty_tree())
                    stack.append(terminal_tree)
                    continue

                parent_tree = stack.pop()
                
                if label.unary_chain is not None:
                    for uc in reversed(label.unary_chain.split(ujoiner)):
                        terminal_tree = C_Tree(uc, [terminal_tree])
                
                # print(">> running l on", parent_tree)
                if parent_tree.children[1].label == C_NONE_LABEL:
                    # print("replacing",parent_tree.children[1],"with",terminal_tree)
                    parent_tree.children[1] = terminal_tree
                else:
                    # print("combining",parent_tree.children[1],"with",terminal_tree)
                    parent_tree.children[1] = combine(parent_tree.children[1], terminal_tree)

                while not parent_tree.has_none_child() and len(stack)>0:
                    parent_tree = stack.pop()
                    parent_tree.update_custody()
                
                stack.append(parent_tree)

            elif op.startswith("R"):
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
                # get the non terminal (or non terminals)
                if ">" in label.last_common:
                    nt = label.last_common.split(">")[0]
                    label.last_common = ">".join(label.last_common.split(">")[1:])
                else:
                    nt = label.last_common
                
                if len(stack)>0:
                    # create a new tree T with label=nt children=<bottom of the stack children>
                    # and replace the rightmost children of the bottom of the stack with T
                    r_child = C_Tree(nt, copy.deepcopy(stack[-1].children))
                    # print(">> running L for rchild",r_child,"and into",stack[-1])

                    stack[-1].children[1] = r_child
                    stack[-1].update_custody()

                    # append it to the bottom of the stack again as it is the new rightmost node
                    stack.append(r_child)
                else:
                    stack.append(C_Tree(nt, [C_Tree.empty_tree(), C_Tree.empty_tree()]))
    
    # get the tree with all the words (hope for the best)
    final_tree = stack.pop()
    try:
        while(len(final_tree.get_terminals()) < len(l_in)):
            final_tree = stack.pop()
    except:
        print(l_in)

    if final_tree.label == "-ROOT-" and len(final_tree.children[0].get_terminals())==len(final_tree.get_terminals()):
        final_tree.inherit_tree(force=True)

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
                if len(stack) > 0 :
                    l_child = stack.pop() if len(stack) > 0 else None
                    r_child = stack.pop() if len(stack) > 0 else None
                    
                    new_children = [l_child] if r_child is None else [r_child, l_child]
                    p_tree  = C_Tree(nt, children=new_children)
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
                    l_child = stack.pop() if len(stack) > 0 else None
                    r_child = stack.pop() if len(stack) > 0 else None
                    
                    new_children = [l_child] if r_child is None else [r_child, l_child]
                    p_tree  = C_Tree(nt, children=new_children)
                    
                    p_tree.update_custody()
                    stack.append(p_tree)

    final_tree = stack.pop()
    final_tree.inherit_tree(force=True)
    return final_tree

class C_Tetratag(ACEncoding):
    def __init__(self, separator, unary_joiner, mode, binary_direction, binary_marker="*"):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.mode = mode
        self.binary_marker = binary_marker
        self.binary = True
        self.binary_direction = binary_direction

    def __str__(self):
        return "Tetratag Encoding "+ self.mode+\
            (f" binary{self.binary_direction}" if self.binary else "")
    
    def encode(self, constituent_tree: C_Tree):
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        # print(f"collapsed tree: {constituent_tree}")
        if self.binary_direction=="R":
            constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
        elif self.binary_direction=="L":
            constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
        else:
            raise Exception("Binary direction not supported")
        # print(constituent_tree)
        if self.mode == "inorder":
            constituent_tree.add_root_node()
            return encode_inorder(constituent_tree, self.separator, self.unary_joiner)
        elif self.mode == "preorder":
            constituent_tree.add_root_node()
            return encode_preorder(constituent_tree, self.separator, self.unary_joiner)
        elif self.mode == "postorder":
            constituent_tree.add_root_node()
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
        final_tree = final_tree.children[0]
        return final_tree