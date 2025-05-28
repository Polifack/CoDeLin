from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_LEFT_DESC_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
from codelin.models.const_label import C_Label
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.const_tree import C_Tree
from copy import deepcopy

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

class C_LeftDescendant(ACEncoding):
    def __init__(self, separator, unary_joiner, binary_direction, look_behind, binary_marker):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.binary=True
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction
        self.look_behind = look_behind

    def __str__(self):
        return "Left Descendant Encoding binary"+self.binary_direction+(" look-behind" if self.look_behind else "")

    def encode(self, constituent_tree: C_Tree):
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        
        if self.binary_direction == "R":
            constituent_tree = C_Tree.to_binary_right(constituent_tree, self.binary_marker)     
        elif self.binary_direction == "L":
            constituent_tree = C_Tree.to_binary_left(constituent_tree, self.binary_marker)
        else:
            raise Exception("Binary direction not supported")
        
        constituent_tree.add_end_node() 
        constituent_tree.precompute_lmost_child()
        lc_tree = LinearizedTree.empty_tree()
        leaf_paths = constituent_tree.path_to_leaves_nodes()

        for i in range(0, len(leaf_paths)-1):
            path_a = leaf_paths[i]
            path_b = leaf_paths[i+1]
           
            word_node = path_a[-1]
            word = word_node.label
            postag = path_a[-2].label

            unary_chain, postag = self.get_unary_chain(postag)
            postag, feats = self.get_features(postag)
            
            j = 0
            while j < len(path_a) and j < len(path_b) and path_a[j] is path_b[j]:
                j += 1

            last_common = path_a[j - 1].label
            n_commons = sum(1 for k in range(j) if path_a[k]._lmost_child == word_node)

            last_common = self.clean_last_common(last_common)
            c_label = C_Label(n_commons, last_common, unary_chain, C_LEFT_DESC_ENCODING,
                            self.separator, self.unary_joiner)
            lc_tree.add_row(word, postag, feats, c_label)
            
        lc_tree.labels[-1].last_common="-NONE-"
        if self.look_behind:
            lc_tree = LinearizedTree.to_look_behind(lc_tree)

        return lc_tree

    def decode(self, linearized_tree):
        # Check valid labels 
        if not linearized_tree:
            print("[*] Error while decoding: Null tree.")
            return
        
        if self.look_behind:
            linearized_tree = LinearizedTree.undo_look_behind(linearized_tree)

        postags = []
        words = []

        tree = C_Tree(C_ROOT_LABEL, [])
        
        open_gaps_stack = []
        current_level = tree
        open_gaps_stack.append(current_level)

        for word, postag, feats, label in linearized_tree.iterrows():
            last_nt = label.last_common
            unary_chain = label.unary_chain
            n_gaps = label.n_commons

            node = C_Tree(postag, children=[C_Tree(word)])

            # build leaf unary chain
            leaf_unary_chain = unary_chain.split(self.unary_joiner) if unary_chain else []
            if len(leaf_unary_chain) > 0:
                for unary in reversed(leaf_unary_chain):
                    node = C_Tree(unary, children=[node])
            
            # create the open gaps. if no gaps to create, just add the node to the tree
            # at the current level
            insert_level = open_gaps_stack.pop() if open_gaps_stack else C_Tree(C_NONE_LABEL, [])
            old_insert_level = insert_level
            while insert_level.parent and insert_level.parent.parent and len(insert_level.children) == 2:
                insert_level = insert_level.parent
            
            if len(insert_level.children) == 2:
                insert_level = old_insert_level
                rightmost_subtree = insert_level.r_child()
                new_subtree = C_Tree(C_NONE_LABEL, [])
                for _ in range(n_gaps):
                    new_subtree.add_child(C_Tree(C_NONE_LABEL, []))
                    new_subtree = new_subtree.r_child()
                
                new_subtree.add_child(rightmost_subtree)
                new_subtree.add_child(node)
                insert_level.children[-1] = new_subtree
                open_gaps_stack.append(insert_level)  
            
            else:
                for _ in range(n_gaps):
                    if len(insert_level.children)< 2 and insert_level.label not in postags and insert_level.label not in words:
                        insert_level.add_child(C_Tree(C_NONE_LABEL, []))
                    insert_level = insert_level.r_child()
                insert_level.add_child(node)
                open_gaps_stack.append(insert_level)

            current_level = insert_level
            while current_level.parent and len(current_level.children) == 2 and current_level.parent.label != C_ROOT_LABEL:
                current_level = current_level.parent
            if last_nt == "-NONE-" or last_nt in words or last_nt in postags:
                continue
            else:
                current_level.label = current_level.label + C_CONFLICT_SEPARATOR + last_nt if current_level.label != C_NONE_LABEL else last_nt
            postags.append(postag)
            words.append(word)

        final_tree = tree.l_child()

        final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        final_tree = final_tree.postprocess_tree()

        return final_tree