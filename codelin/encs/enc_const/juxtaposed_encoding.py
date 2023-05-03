from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_JUXTAPOSED_ENCODING, C_RELATIVE_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree
from dataclasses import dataclass


import re

@dataclass
class Action:
    name: str
    target_node: int
    parent_label: str|None
    new_label: str|None

empty_tree = C_Tree(C_NONE_LABEL)

def get_level_of_subtree(t, st):
    '''
    Given a tree and a subtree representing the rightmost 
    subtree of the tree, it returns the level of the subtree
    '''
    if t == st:
        return 0
    else:
        return 1 + get_level_of_subtree(t.children[-1], st)

def _get_action_list(tree):
    '''
    Given a tree, it returns the action that caused the last subtree to be
    attached to the tree. The tree must have NO unary chains (i.e. it must
    collapse them first, including part of speech tags.)
    '''
    last_postag = tree.get_terminals()[-1].parent
    last_word   = last_postag.children[0]
    siblings  = last_postag.parent.children[:-1] if last_postag.parent is not None else []
    
    if siblings != []:
        last_subtree = last_postag
        last_subtree_siblings = siblings
        parent_label = None
    else:
        last_subtree = last_postag.parent
        
        if last_subtree is None:
            return last_word.label, last_postag.label, \
                Action(name="attach", target_node=1, parent_label=None, new_label=None), None
        
        last_subtree_siblings = last_subtree.parent.children[:-1] if last_subtree.parent is not None else []
        parent_label = last_subtree.label

    if last_subtree.parent is None:
        return last_word.label, last_postag.label, \
            Action(name="attach", target_node=1, parent_label=parent_label, new_label=None), None 

    elif len(last_subtree_siblings)==1 and not last_subtree_siblings[0].is_preterminal():
        target_node_depth = get_level_of_subtree(tree, last_subtree)
        
        new_label = last_subtree.parent.label
        target_node = last_subtree_siblings[0]
        grand_parent = last_subtree.parent.parent
        if grand_parent is None:
            tree = target_node
            target_node.parent = None
        else:
            grand_parent.children = [target_node if c == last_subtree.parent else c for c in grand_parent.children]
            target_node.parent = grand_parent
        
        return last_word.label, last_postag.label, \
            Action(name="juxtapose", target_node = target_node_depth, parent_label = parent_label, new_label = new_label), tree
    
    else:
        target_node_depth = get_level_of_subtree(tree, last_subtree)

        target_node = last_subtree.parent
        target_node.children.remove(last_subtree)
        
        return last_word.label, last_postag.label, \
            Action(name="attach", target_node = target_node_depth, parent_label = parent_label, new_label = None), tree

def oracle_action_sequence(t):
    if t is None:
        return []
    
    if len(t.children)==0 or (len(t.children)==1 and t.children[0].is_preterminal()):
        p = t.children[0].label
        w = t.children[0].children[0].label
    
        a = Action(name="attach", target_node=0, parent_label=t.label, new_label=None)
        
        action_string = a.name + ">>" + str(a.parent_label) + (">>" + str(a.new_label) if a.new_label is not None else "")
        l = C_Label(nc = a.target_node, lc = action_string, uc = None, sp="_", et = C_JUXTAPOSED_ENCODING, uj="+")
        lin_tree_row = (w, p, l)

        return [lin_tree_row]
    
    else:
        w, p, a, t = _get_action_list(t)

        action_string = a.name + ">>" + str(a.parent_label) + (">>" + str(a.new_label) if a.new_label is not None else "")
        l = C_Label(nc = a.target_node, lc = action_string, uc = None, sp="_", et = C_JUXTAPOSED_ENCODING, uj="+")
        lin_tree_row = (w, p, l)
        
        return oracle_action_sequence(t) + [lin_tree_row]

class C_JuxtaposedEncoding(ACEncoding):
    def __init__(self, separator, unary_joiner, reverse, binary, binary_direction, binary_marker):        
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.reverse = reverse
        self.binary = binary
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction

    def __str__(self):
        return "Juxtaposed Encoding"

    def encode(self, constituent_tree):
        lc_tree = LinearizedTree.empty_tree()
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        labels = oracle_action_sequence(constituent_tree)
        for l in labels:
            print(l)
        pass

    def decode(self, linearized_tree):
        pass