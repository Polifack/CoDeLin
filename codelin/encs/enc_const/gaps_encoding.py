from codelin.encs.abstract_encoding import ACEncoding
from codelin.utils.constants import C_GAPS_ENCODING, C_ROOT_LABEL, C_CONFLICT_SEPARATOR, C_NONE_LABEL
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


class C_GapsEncoding(ACEncoding):
    def __init__(self, separator, unary_joiner, binary_direction, reverse, binary_marker, mode):
        self.separator = separator
        self.unary_joiner = unary_joiner
        self.binary_marker = binary_marker
        self.binary_direction = binary_direction
        self.mode = mode
        self.reverse = reverse

        print("[*] Constituent Gaps Based Encoding initialized.")
        print(f"[*] Separator: {separator}")
        print(f"[*] Unary Joiner: {unary_joiner}")
        print(f"[*] Binary Marker: {binary_marker}")
        print(f"[*] Binary Direction: {binary_direction}")
        print(f"[*] Mode: {mode}")
        print(f"[*] Reverse: {reverse}")


    def __str__(self):
        return "Constituent Gaps Based Encoding"

    def encode(self, constituent_tree):
        constituent_tree = deepcopy(constituent_tree)
        if self.reverse:
            constituent_tree.reverse_tree()
        
        constituent_tree = constituent_tree.collapse_unary(self.unary_joiner)
        
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
        unary_chain = None
        features = None

        for node in nodes:
            if node.is_preterminal():
                postag = node.label
                unary_chain, postag = self.get_unary_chain(postag)
                postag, features = self.get_features(postag)
            
            elif node.is_terminal():
                word     = node.label
                node     = node.parent
                n_gaps   = 0
                
                if self.mode == "close":
                    while node.parent and node.is_right_child():
                        n_gaps += 1
                        node    = node.parent
                
                elif self.mode == "open":
                    while node.parent and node.is_left_child():
                        n_gaps += 1
                        node    = node.parent

            else:
                non_terminal = node.label
                label = C_Label(n_gaps, non_terminal, unary_chain, C_GAPS_ENCODING, self.separator, self.unary_joiner)
                lc_tree.add_row(word, postag, features, label)
                
        
        # last label
        label = C_Label(n_gaps, "$$", unary_chain, C_GAPS_ENCODING, self.separator, self.unary_joiner)
        lc_tree.add_row(word, postag, features, label)
        if self.reverse:
            lc_tree.reverse_tree(ignore_bos_eos=False)
        return lc_tree

    def decode_open_gaps(self, linearized_tree):
        linearized_tree = deepcopy(linearized_tree)
        if not linearized_tree:
            print("[*] Error while decoding: Null tree.")
            return
        
        postags = []
        words = []

        tree = C_Tree(C_ROOT_LABEL, [])
        open_gaps_stack = []
        current_level = tree
        open_gaps_stack.append(current_level)

        if self.reverse:
            linearized_tree.reverse_tree(ignore_bos_eos=False)

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
            # at the current level (rightmost open gap)
            insert_level = open_gaps_stack.pop() if open_gaps_stack else C_Tree(C_NONE_LABEL, [])
            old_insert_level = insert_level
            while insert_level.parent and insert_level.parent.parent and len(insert_level.children) == 2:
                insert_level = insert_level.parent
            
            if len(insert_level.children) == 2:
                insert_level = old_insert_level
                # perform a juxtapose
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

            # set the label of the deepest common non terminal. we know what the deepest common non terminal
            # is because we are building the tree from the bottom up
            current_level = insert_level
            while current_level.parent and len(current_level.children) == 2 and current_level.parent.label != C_ROOT_LABEL:
                current_level = current_level.parent
            if last_nt == "$$":
                continue
            else:
                current_level.label = current_level.label + C_CONFLICT_SEPARATOR + last_nt if current_level.label != C_NONE_LABEL else last_nt
            postags.append(postag)
            words.append(word)
        # C_Tree.pretty_print(tree)
        final_tree = tree.l_child()
        if self.reverse:
            final_tree.reverse_tree()
        final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)
        return final_tree
    
    def decode_close_gaps(self, linearized_tree):
        linearized_tree = deepcopy(linearized_tree)
        nodes_stack = []

        if self.reverse:
            linearized_tree.reverse_tree(ignore_bos_eos=False)

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
            
            for _ in range(n_gaps):
                stack_top = nodes_stack.pop() if nodes_stack else C_Tree(C_NONE_LABEL)
                node = merge_if_free(last_nt, stack_top, node)
           
            if last_nt == "$$":
                continue

            node = C_Tree(last_nt, children=[node, C_Tree(C_NONE_LABEL)])
            nodes_stack.append(node)
        
        while len(nodes_stack) > 0:
            # merge node with stack top
            stack_top = nodes_stack.pop()
            node = merge_if_free(C_ROOT_LABEL, stack_top, node)

        final_tree = node
        if self.reverse:
            final_tree.reverse_tree()
        final_tree = C_Tree.restore_from_binary(final_tree, self.binary_marker)
        final_tree = final_tree.uncollapse_unary(self.unary_joiner)

        return final_tree

    def decode(self, linearized_tree):
        # Check valid labels 
        if not linearized_tree:
            print("[*] Error while decoding: Null tree.")
            return
        if self.mode == "open":
            decoded_tree = self.decode_open_gaps(linearized_tree)
            return decoded_tree

        if self.mode == "close":
            decoded_tree = self.decode_close_gaps(linearized_tree)
            return decoded_tree