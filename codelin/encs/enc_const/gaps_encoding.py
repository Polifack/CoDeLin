from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_GAPS_ENCODING, C_RELATIVE_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree

import re

def merge_if_free(nt, parent, children):
    '''
    Given the label of a non-terminal node, a parent node and a children node,
    it merges the children node with the parent node if the parent node has a
    free gap in the right side of the tree. Otherwise, it creates a new node
    with the given label and the parent and children nodes as children.
    '''
    if C_NONE_LABEL in [c.label for c in parent.children]:
        parent.children[1] = children        
    else:
        parent = C_Tree(nt, children=[parent, children])
    return parent


class C_GapsEncoding(ACEncoding):
    def __init__(self, separator, unary_joiner, reverse, binary, binary_direction, binary_marker):
        if not binary:
            raise Exception("Gaps encoding only works with binary trees")
        
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.reverse = reverse
        self.binary = binary
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction

    def __str__(self):
        return "Constituent Gaps Based Encoding"

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
        
        nodes = []
        C_Tree.inorder(constituent_tree, lambda x: nodes.append(x))
        postag = None

        for node in nodes:
            if node.is_preterminal():
                postag = node.label
                unary_chain, postag = self.get_unary_chain(postag)
                postag, features = self.get_features(postag)
            
            elif node.is_terminal():
                word     = node.label
                node     = node.parent
                n_right  = 0
                while node.parent and node.is_right_child():
                    n_right += 1
                    node    = node.parent

            else:
                non_terminal = node.label
                label = C_Label(n_right, non_terminal, unary_chain, C_GAPS_ENCODING, self.separator, self.unary_joiner)
                lc_tree.add_row(word, postag, features, label)
                
        
        # last label
        label = C_Label(n_right, "$$", unary_chain, C_GAPS_ENCODING, self.separator, self.unary_joiner)
        lc_tree.add_row(word, postag, features, label)
        
        if self.reverse:
            lc_tree.reverse_tree(ignore_bos_eos=False)

        return lc_tree

    def decode(self, linearized_tree):
        # Check valid labels 
        if not linearized_tree:
            print("[*] Error while decoding: Null tree.")
            return
        
        nodes_stack = []
        for word, postag, feats, label in linearized_tree.iterrows():
            last_nt = label.last_common
            unary_chain = label.unary_chain
            n_right = label.n_commons

            node = C_Tree(postag, children=[C_Tree(word)])

            # build leaf unary chain
            leaf_unary_chain = unary_chain.split(self.unary_joiner) if unary_chain else []
            if len(leaf_unary_chain) > 0:
                for unary in reversed(leaf_unary_chain):
                    node = C_Tree(unary, children=[node])

            for _ in range(n_right):
                stack_top = nodes_stack.pop()
                node = merge_if_free(last_nt, stack_top, node)

            if last_nt == "$$":
                continue

            node = C_Tree(last_nt, children=[node, C_Tree(C_NONE_LABEL)])
            nodes_stack.append(node)

        final_tree = node
        if self.binary:
            final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        
        return final_tree