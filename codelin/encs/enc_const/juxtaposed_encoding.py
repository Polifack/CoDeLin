from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_JUXTAPOSED_ENCODING, C_RELATIVE_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree
from dataclasses import dataclass
import copy
import re

@dataclass
class Action:
    name: str
    target_node: int
    parent_label: str|None
    new_label: str|None

empty_tree = C_Tree(C_NONE_LABEL)

def attach(new_rightmost_subtree, target_node, parent_label):
    '''
    Given a target node, a input token and (optionally) a parent label
    this function will create a new subtree as (parent_label(current_token))
    and attach it as the new rightmost subtree of the target node.
    '''
    if parent_label is not None:
        new_rightmost_subtree = C_Tree(parent_label, children=[new_rightmost_subtree])
        target_node.add_child(new_rightmost_subtree)
        return new_rightmost_subtree
    
    target_node.add_child(new_rightmost_subtree)

def juxtapose(new_subtree, target_node, parent_label, new_label):
    '''
    Given a target node, a parent label (optionally) and a new label this function 
    will create a new subtree as (parent_label(target_node)) and a new node with label
    new_label and children as the target node and the newly created subtree. This new 
    node will replace the target node in the tree.
    '''
    if parent_label is not None:
        new_subtree = C_Tree(parent_label, children=[new_subtree])

    if target_node.parent is not None:
        cpy_target_node = copy.deepcopy(target_node)
        new_node = C_Tree(new_label, children=[cpy_target_node, new_subtree])
        parent_node = target_node.parent
        parent_node.children[parent_node.children.index(target_node)] = new_node
    
    else:
        # we are at the root node
        cpy_target_node = copy.deepcopy(target_node)
        new_node = C_Tree(new_label, children=[cpy_target_node, new_subtree])
        target_node.label = new_node.label
        target_node.children = new_node.children

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
        lin_tree_row = (w, p, a)

        return [lin_tree_row]
    
    else:
        w, p, a, t = _get_action_list(t)
        lin_tree_row = (w, p, a)
        
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
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        
        if self.binary:
            if self.binary_direction == "R":
                constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
            elif self.binary_direction == "L":
                constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
            else:
                raise Exception("Binary direction not supported")
        
        lc_tree = LinearizedTree.empty_tree()
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        seq = oracle_action_sequence(constituent_tree)

        for w,p,a in seq:
            uc, p = self.get_unary_chain(p)
            p, f = self.get_features(p)
            
            lc_str = "an="+str(a.name)+\
                ("[;]"+"pl="+str(a.parent_label) if a.parent_label is not None else "")+\
                    ("[;]"+"nl="+str(a.new_label) if a.new_label is not None else "")
            l = C_Label(nc=a.target_node, lc=lc_str, uc=uc, et=C_JUXTAPOSED_ENCODING, sp=self.separator, uj=self.unary_joiner)
            
            lc_tree.add_row(w, p, f, l)
        
        return lc_tree

    def decode(self, linearized_tree):
        t = C_Tree(C_NONE_LABEL)
        st = t
        for word, postag, feats, label in linearized_tree.iterrows():
            # reset level
            t = st
            
            # extract action info from label
            target_node = label.n_commons
            action  = label.last_common.split("[;]")
            action_name = None
            parent_label = None
            new_label = None
            for element in action:
                n, v = element.split("=")
                if n == "an":
                    action_name = v
                elif n == "pl":
                    parent_label = v
                elif n == "nl":
                    new_label = v
            
            action = Action(name=action_name, target_node=target_node, parent_label=parent_label, new_label=new_label)

            # build terminal
            term_tree = C_Tree(postag,[C_Tree(word)])
            if label.unary_chain is not None:
                for uc in reversed(label.unary_chain.split(self.unary_joiner)):
                    term_tree = C_Tree(uc, [term_tree])
            
            # take action
            target_level = action.target_node
            
            # descend
            while target_level > 0 and len(t.children) > 0:
                t = t.children[-1]
                target_level -= 1
            
            if action.name == "attach":
                attach(term_tree, t, action.parent_label)
            
            elif action.name == "juxtapose":
                t = juxtapose(term_tree, t, action.parent_label, action.new_label)

        final_tree = st.children[0]
        if self.binary:
            final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        
        return final_tree