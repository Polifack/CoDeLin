from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_ABSOLUTE_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree

import re
import copy

class C_NaiveAbsoluteEncoding(ACEncoding):
    def __init__(self, separator, unary_joiner, reverse, binary, binary_direction=None, binary_marker=None):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.reverse = reverse
        self.binary = binary
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction

    def __str__(self):
        return "Constituent Naive Absolute Encoding"

    def encode(self, constituent_tree):
        if self.reverse:
            constituent_tree.reverse_tree()
        
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        if self.binary:
            if self.binary_direction == "R":
                constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)
            elif self.binary_direction == "L":
                constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
            else:
                raise Exception("Binary direction not supported")
        
        leaf_paths = constituent_tree.path_to_leaves()
        lc_tree = LinearizedTree.empty_tree()
        for i in range(0, len(leaf_paths)-1):
            path_a = leaf_paths[i]
            path_b = leaf_paths[i+1]

            last_common = ""
            n_commons   = 0
            for a,b in zip(path_a, path_b):
                if (a!=b):
                    # Remove the digits and aditional feats in the last common node
                    last_common = self.clean_last_common(last_common)

                    # Get word and POS tag
                    word = path_a[-1]
                    postag = path_a[-2]
                    
                    # Build the Leaf Unary Chain
                    unary_chain, postag = self.get_unary_chain(postag)
                    
                    # Clean the POS Tag and extract additional features
                    postag, feats = self.get_features(postag)

                    c_label = C_Label(n_commons, last_common, unary_chain, C_ABSOLUTE_ENCODING, 
                                                self.separator, self.unary_joiner)
                    lc_tree.add_row(word, postag, feats, c_label)
                
                    break
                
                n_commons  += len(a.split(self.unary_joiner))
                last_common = a
        
        if self.reverse:
            lc_tree.reverse_tree(ignore_bos_eos=False)
    
        return lc_tree

    def decode(self, linearized_tree):
        # Check valid labels
        if not linearized_tree:
            print("[!] Error while decoding: Null tree.")
            return

        # Create constituent tree
        tree = C_Tree(C_ROOT_LABEL, [])
        current_level = tree

        old_n_commons = 0
        old_level = None

        if self.reverse:
            linearized_tree.reverse_tree(ignore_bos_eos=False)


        for word, postag, feats, label in linearized_tree.iterrows():

            # Descend through the tree until reach the level indicated by last_common
            current_level = tree
            for level_index in range(label.n_commons):
                if (current_level.is_terminal()) or (level_index >= old_n_commons):
                    current_level.add_child(C_Tree(C_NONE_LABEL, []))
                
                current_level = current_level.r_child()

            # Split the Last Common field of the Label in case it has a Unary Chain Collapsed
            label.last_common = label.last_common.split(self.unary_joiner)

            if len(label.last_common) == 1:
                # If current level has no label yet, put the label
                # If current level has label but different than this one, set it as a conflict
                if (current_level.label == C_NONE_LABEL):
                    current_level.label = label.last_common[0].rstrip()
                else:
                    current_level.label = current_level.label + C_CONFLICT_SEPARATOR + label.last_common[0]
            else:
                current_level = tree
                
                # Descend to the beginning of the Unary Chain and fill it
                descend_levels = max(label.n_commons - (len(label.last_common)) + 1, 1)
                
                for level_index in range(descend_levels):
                    current_level = current_level.r_child() if current_level.r_child() is not None else current_level
                
                for i in range(len(label.last_common)-1):
                    if (current_level.label == C_NONE_LABEL):
                        current_level.label = label.last_common[i]
                    else:
                        current_level.label = current_level.label + C_CONFLICT_SEPARATOR + label.last_common[i]
                    
                    current_level = current_level.r_child() if current_level.r_child() is not None else current_level

                # If we reach a POS tag, set it as child of the current chain
                if current_level.is_preterminal():
                    temp_current_level = copy.deepcopy(current_level)
                    current_level.label = label.last_common[i+1]
                    current_level.children = [temp_current_level]
                else:
                    current_level.label=label.last_common[i+1]
            
            # Fill POS tag in this node or previous one
            if (label.n_commons >= old_n_commons):
                current_level.fill_pos_nodes(postag, word, label.unary_chain, self.unary_joiner)
            else:
                old_level.fill_pos_nodes(postag, word, label.unary_chain, self.unary_joiner)

            old_n_commons=label.n_commons
            old_level=current_level

        tree.inherit_tree()
        if self.reverse:
            tree.reverse_tree()
        if self.binary:
            tree = C_Tree.restore_from_binary(tree, self.binary_marker)
        return tree