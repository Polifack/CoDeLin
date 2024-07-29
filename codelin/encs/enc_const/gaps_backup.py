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
                n_gaps  = 0
                
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
        current_level = tree
        if self.reverse:
            linearized_tree.reverse_tree(ignore_bos_eos=False)

        for word, postag, feats, label in linearized_tree.iterrows():
            last_nt = label.last_common
            unary_chain = label.unary_chain
            n_gaps = label.n_commons
            
            print(word, postag, label)
            postags.append(postag)
            words.append(word)

            node = C_Tree(postag, children=[C_Tree(word)])

            # build leaf unary chain
            leaf_unary_chain = unary_chain.split(self.unary_joiner) if unary_chain else []
            if len(leaf_unary_chain) > 0:
                for unary in reversed(leaf_unary_chain):
                    node = C_Tree(unary, children=[node])
            
            # create the open gaps
            for _ in range(n_gaps):
                print(current_level)
                if len(current_level.children)< 2 and current_level.label not in postags and current_level.label not in words:
                    current_level.add_child(C_Tree(C_NONE_LABEL, []))
                current_level = current_level.r_child()

            # ensure that we are inserting in a node that has less than 2 children
            while len(current_level.children) >= 2:
                current_level = current_level.r_child()

            print(current_level)
            # insert the node
            current_level.add_child(node)
            
            # insert the non terminal at the first -none- label
            while current_level.label != "-NONE-":
                if not current_level.parent:
                    break
                current_level = current_level.parent
            
            # fix for last label
            if not current_level.parent:
                current_level = current_level.l_child()
            
            current_level.label = last_nt if last_nt!="$$" else current_level.label
            C_Tree.pretty_print(tree)
            print(15*"-")
        
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