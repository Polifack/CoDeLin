from codelin.utils.constants import C_END_LABEL, C_START_LABEL, C_NONE_LABEL, C_ROOT_LABEL
from codelin.utils.constants import C_CONFLICT_SEPARATOR, C_STRAT_MAX, C_STRAT_FIRST, C_STRAT_LAST, C_NONE_LABEL
import copy


class C_Tree:
    def __init__(self, label, children=[], feats=None):
        self.parent = None
        self.label = label
        self.children = []
        self.features = feats

        self.add_child(children)

# Adders and deleters
    def add_child(self, child):
        '''
        Function that adds a child to the current tree
        '''
        if type(child) is list:
            for c in child:
                self.add_child(c)
        elif type(child) is C_Tree:
            self.children.append(child)
            child.parent = self

        else:
            raise TypeError("[!] Child must be a ConstituentTree or a list of Constituent Trees")

    def add_left_child(self, child):
        '''
        Function that adds a child to the left of the current tree
        '''
        if type(child) is list:
            for c in child:
                self.children = [c] + self.children
                c.parent = self
        elif type(child) is C_Tree:
            self.children = [child] + self.children
            child.parent = self

        else:
            raise TypeError("[!] Child must be a ConstituentTree or a list of Constituent Trees")

    def add_child_at_index(self, child, index):
        '''
        Function that adds a child to the left of the current tree
        '''
        if type(child) is list:
            for c in child:
                c.parent = self
            self.children = self.children[:index] + child + self.children[len(self.children)-(index+1):]
                
        elif type(child) is C_Tree:
            self.children = self.children[:index]+[child]+self.children[index+1:]
            child.parent = self

        else:
            raise TypeError("[!] Child must be a ConstituentTree or a list of Constituent Trees")

    def del_child(self, child):
        '''
        Function that deletes a child from the current tree
        without adding its children to the current tree
        '''
        if type(child) is not C_Tree:
            raise TypeError("[!] Child must be a ConstituentTree")

        self.children.remove(child)
        child.parent = None

    def set_dummy_preterminals(self):
        '''
        Creates preterminal dummy nodes with label _ in case the given trees do not have them
        '''
        for node in self.get_terminals():
            node_parent = node.parent
            temp_node = C_Tree(C_NONE_LABEL, [node])
            node.parent = temp_node
            node_parent.children[node_parent.children.index(node)] = temp_node
                

# Getters
    def r_child(self):
        '''
        Function that returns the rightmost child of a tree
        '''
        return self.children[len(self.children)-1] if len(self.children)>0 else None

    def rmost_child(self):
        '''
        Returns the rightmost children of a tree and all its subtrees
        '''
        tree = self
        while tree.children is not None and tree.children != []:
            tree = tree.children[-1]
        return tree
    
    def precompute_rmost_child(self):
        """
        Recursively computes and stores the rightmost child for each subtree.
        Adds `_rmost_child` attribute to every node.
        """
        if not self.children:
            self._rmost_child = self
            return self

        # Compute for all children first (bottom-up)
        for child in self.children:
            child.precompute_rmost_child()

        # The rightmost child of this node is the rightmost child's _rmost_child
        self._rmost_child = self.children[-1]._rmost_child
        return self._rmost_child
    
    def l_child(self):
        '''
        Function that returns the leftmost child of a tree
        '''
        return self.children[0]
    
    def lmost_child(self):
        '''
        Returns the rightmost children of a tree and all its subtrees
        '''
        tree = self
        while tree.children is not None and tree.children != []:
            tree = tree.children[0]
        return tree
    
    def precompute_lmost_child(self):
        """
        Recursively computes and stores the leftmost child for each subtree.
        Adds `_lmost_child` attribute to every node.
        """
        if not self.children:
            self._lmost_child = self
            return self

        # Compute for all children first (bottom-up)
        for child in self.children:
            child.precompute_lmost_child()

        # The rightmost child of this node is the leftmost child's _lmost_child
        self._lmost_child = self.children[0]._lmost_child
        return self._lmost_child
    
    def r_siblings(self):
        '''
        Function that returns the right siblings of a tree
        '''
        if self.parent is None:
            return []
        return self.parent.children[self.parent.children.index(self)+1:]

    def l_siblings(self):
        '''
        Function that returns the left siblings of a tree
        '''
        return self.parent.children[:self.parent.children.index(self)]

    def get_root(self):
        '''
        Function that returns the root of a tree
        '''
        if self.parent is None:
            return self
        else:
            return self.parent.get_root()

    def get_feature_names(self):
        '''
        Returns a set containing all feature names
        for the tree
        '''
        feat_names = set()

        for child in self.children:
            feat_names = feat_names.union(child.get_feature_names())
        if self.features is not None:
            feat_names = feat_names.union(set(self.features.keys()))

        return feat_names            

    def get_terminals(self):
        '''
        Function that returns the terminal nodes of a tree
        '''
        if self.is_terminal():
            return [self]
        else:
            return [node for child in self.children for node in child.get_terminals()]

    def get_preterminals(self):
        '''
        Function that returns the preterminal nodes of a tree
        '''
        if self.is_preterminal():
            return [self]
        else:
            return [node for child in self.children for node in child.get_preterminals()]

    def get_words(self):
        '''
        Returns the labels of the terminal nodes of the tree
        '''
        if self.is_terminal():
            return [self.label]
        else:
            return [node for child in self.children for node in child.get_words()]
    
    def get_non_terminals(self):
        '''
        Returns the unique labels of the non-terminal nodes of the tree
        '''
        non_terminals = set()
        C_Tree.inorder(self, lambda x: non_terminals.add(str(x.label)) if x.is_non_terminal() else None)
        return non_terminals

    def get_sentence(self):
        return " ".join([x.label for x in self.get_terminals()])


# Tree stats
    def depth(self, ignore_postags=True):
        '''
        Function that returns the maximum depth of a tree
        '''
        if self.is_terminal():
            return 0
        if ignore_postags and self.is_preterminal():
            return 0
        else:
            return 1 + max([child.depth() for child in self.children])
        
    def width(self):
        '''
        Function that returns an array of the width of each
        level of a tree
        '''
        nodes = {}
        def fill_dict(node, level):
            if level not in nodes:
                nodes[level] = []
            nodes[level].append(node)
            for child in node.children:
                fill_dict(child, level+1)

        fill_dict(self, 0)
        
        # get the length of each level
        for level in nodes.keys():
            nodes[level] = len(nodes[level])
        return nodes
    
    def average_branching_factor(self):
        '''
        Function that returns the average branching factor of a tree and all of its children
        '''
        nodes = []
        C_Tree.inorder(self, lambda x: nodes.append(x))
        
        branching = []
        for node in nodes:
            if node.is_terminal() or node.is_root() or node.is_preterminal():
                continue
            else:
                branching.append(len(node.children))
        
        return sum(branching)/len(branching) if len(branching) > 0 else 0
    
    def branching(self):
        '''
        Compute the branching of a tree by counting non-terminal nodes that 
        are in the left or right half of their parent's children.
        '''

        nodes = []
        C_Tree.inorder(self, lambda x: nodes.append(x))

        branching = []
        for node in nodes:
            if node.is_terminal() or node.is_preterminal():
                continue
            
            parent = node.parent
            if parent:
                siblings = parent.children
                if len(siblings) == 1:
                    continue  # Ignore single children
                idx = siblings.index(node)
                midpoint = len(siblings)/2

                if idx < midpoint:
                    branching.append("L")
                else:
                    branching.append("R")

        bl = branching.count("L")
        br = branching.count("R")

        total = bl + br
        bl_percentage = (bl / total) * 100 if total > 0 else 0
        br_percentage = (br / total) * 100 if total > 0 else 0

        return {"L": bl_percentage, "R": br_percentage}

    
# Checkers
    def is_right_child(self):
        '''
        Returns if a given subtree is the 
        rightmost child of its parent
        '''
        return self.parent is not None and len(self.parent.children)>1 and self.parent.children.index(self)==len(self.parent.children)-1

    def is_rightmost_word_in_subtree(self, subtree, idx):
        '''
        Given the index of a word and a subtree in the current tree
        it returns true or false depending if the word is the rightmost
        terminal node in said subtree
        '''
        word = self.get_terminals()[idx]
        rmost_child = subtree.rmost_child()
        return word == rmost_child

    def is_left_child(self):
        '''
        Returns if a given subtree is the
        leftmost child of its parent
        '''
        return self.parent is None or self.parent.children.index(self)==0
    
    def is_leftmost_word_in_subtree(self, subtree, idx):
        '''
        Given the index of a word and a subtree in the current tree
        it returns true or false depending if the word is the rightmost
        terminal node in said subtree
        '''
        word = self.get_terminals()[idx]
        lmost_child = subtree.lmost_child()
        return word == lmost_child

    def has_none_child(self):
        '''
        Returns true if a given son of the tree
        has a C_NONE_LABEL as child
        '''
        for c in self.children:
            if c.label == C_NONE_LABEL:
                return True
        return False

    def is_root(self):
        '''
        Function that checks if a tree is a root
        '''
        return self.parent is None

    def is_terminal(self):
        '''
        Function that checks if a tree is a terminal
        '''
        return len(self.children) == 0

    def is_preterminal(self):
        '''
        Function that checks if a tree is a preterminal
        '''
        return len(self.children) == 1 and self.children[0].is_terminal()

    def is_non_terminal(self):
        return not (self.is_terminal() or self.is_preterminal())

    def is_unary_chain(self):
        # Returns true if the tree is an intermediate unary chain
        if len(self.children)==1 and not (self.is_preterminal() or self.is_terminal()):
            return True
        else:
            return False


# Tree processing
    # def preorder_iterator(self):
    #     yield self
    #     for child in self.children:
    #         yield from child.preorder_iterator()
    @staticmethod
    def simplify_tree(tree):
        """
        Transforms a tree:
        - Nonterminals become A, B, C...
        - POS tags become P1, P2, P3...
        - Words become w1, w2, w3...
        """
        new_tree = copy.deepcopy(tree)
        words = new_tree.get_terminals()
        postags = new_tree.get_preterminals()



        i=1
        for n in words:
            n.label = "w"+str(i)
            i+=1
        i=1
        for n in postags:
            n.label = "P"+str(i)
            i+=1
        
        i=0
        nts="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        def replace_nonterminals(node):
            nonlocal i  # allows for access outside var instead of scope var
            if not node.is_terminal() and not node.is_preterminal():
                node.label = nts[i]
                i += 1
            for child in node.children:
                replace_nonterminals(child)
        replace_nonterminals(new_tree)
        return new_tree


    def extract_features(self, f_mark = "##", f_sep = "|"):
        # go through all pre-terminal nodes
        # of the tree
        for node in self.get_preterminals():
            if f_mark in node.label:
                node.features = {}
                label = node.label.split(f_mark)[0]
                features   = node.label.split(f_mark)[1]

                node.label = label

                # add features to the tree
                for feature in features.split(f_sep):
                    
                    if feature == "_":
                        continue
                
                    key = feature.split("=")[0]
                    value = feature.split("=")[1]

                    node.features[key]=value

    def clean_tree(self, idx_marker="##"):
        '''
        Removes the features markers from the tree
        '''
        if idx_marker in self.label:
            self.label = self.label.split(idx_marker)[0]

        for child in self.children:
            child.clean_tree(idx_marker)
    
    def get_common_nodes_between_words(self, idx_1, idx_2):
        words = self.get_terminals()
        node_1 = words[idx_1]
        node_2 = words[idx_2]
        
        path_to_leaves_1 = []
        while node_1 is not None:
            path_to_leaves_1.append(node_1)
            node_1 = node_1.parent

        path_to_leaves_2 = []
        while node_2 is not None:
            path_to_leaves_2.append(node_2)
            node_2 = node_2.parent

        common_nodes = []
        for n1 in path_to_leaves_1:
            for n2 in path_to_leaves_2:
                if str(n1) == str(n2):
                    # Safe check to ensure terminal or nonterminal nodes are not added
                    if not (n1.is_terminal() or n1.is_preterminal()):
                        common_nodes.append(n1)
                    break

        return common_nodes

        
    def collapse_unary(self, unary_joiner="[+]", intermediate_only=False):
        '''
        Returns a new tree where the unary chains are replaced
        by a new node where the label is formed by all the 
        members in the unary chain separated by 'unary_joiner' string.

        The algorithm works top-down, this meaning, will declare a unary chain from the
        parent to the children.

        :unary_joiner: character to use in the node labels to join the chain nodes
        :intermediate_only: avoid collapsing nodes that end in leaves
        '''
        if self.is_unary_chain() and (not intermediate_only or not self.children[0].is_preterminal()):
            c = self.children[0]
            label = c.label

            # get all unary chain nodes
            while c.is_unary_chain() and not c.is_preterminal():
                label += unary_joiner + c.children[0].label
                c = c.children[0]

            label = self.label + unary_joiner + label
            children = c.children
            return C_Tree(label, [c.collapse_unary(unary_joiner, intermediate_only) for c in children])
        else:
            return C_Tree(self.label, [c.collapse_unary(unary_joiner, intermediate_only) for c in self.children])


    def uncollapse_unary(self, unary_joiner="[+]"):
        '''
        Returns a new tree where the unary chains are replaced
        by a new node where the label is formed by all the
        members in the unary chain separated by 'unary_joiner' string.
        '''
        if unary_joiner in self.label:
            us = self.label.split(unary_joiner)
            temp_tree = C_Tree(us[0])
            pointer   = temp_tree
            for i in range(1, len(us)):
                pointer.add_child(C_Tree(us[i]))
                pointer = pointer.children[0]
                
            
            pointer.add_child([c.uncollapse_unary(unary_joiner) for c in self.children])
            return temp_tree
        else:
            return C_Tree(self.label, [c.uncollapse_unary(unary_joiner) for c in self.children])

    def remove_preterminals(self):
        '''
        Returns a new tree where the preterminal nodes from the 
        constituent tree are removed.
        '''
        new_child = []
        for child in self.children:
            new_child.append(child.remove_preterminals())
        
        if self.is_preterminal():
            return self.children[0]
        else:
            return C_Tree(self.label, new_child)

    def inherit_tree(self, force=False):
        '''
        Removes the top node of the tree and delegates it
        to its firstborn child. 
        
        (S (NP (NNP John)) (VP (VBD died))) => (NP (NNP John))
        '''
        if len(self.children)>1 and not force:
            return
        self.label = self.children[0].label
        self.children = self.children[0].children

    def add_root_node(self):
        copy_tree = copy.deepcopy(self)
        self.label = C_ROOT_LABEL
        self.children = [copy_tree]
        copy_tree.parent = self

    def add_end_node(self):
        '''
        Function that adds a dummy end node to the 
        rightmost part of the tree
        '''
        self.add_child(C_Tree(C_END_LABEL, []))

    def add_start_node(self):
        '''
        Function that adds a dummy start node with terminal and preterminal to the leftmost
        part of the tree
        '''
        self.add_left_child(C_Tree(C_START_LABEL, [C_Tree(C_START_LABEL, [])]))
                    
    def path_to_leaves(self):
        '''
        Returns the list of paths from the root to the leaves, 
        encoding a level index into nodes to make them unique.
        '''
        def path_to_leaves_rec(t, current_path, paths, idx):
            path = copy.deepcopy(current_path)
            
            if (len(t.children)==0):
                path.append(t.label)
                paths.append(path)
            else:
                path.append(t.label+'['+str(idx)+']')
                for child in t.children:
                    path_to_leaves_rec(child, path, paths, idx)
                    idx+=1
            return paths
        
        self.add_end_node() 
        return path_to_leaves_rec(self, [], [], 0)
    
    def path_to_leaves_nodes(self):
        '''
        Returns the list of tree nodes from the root to the leaves
        '''
        paths = []
        stack = [(self, [])]

        while stack:
            node, path = stack.pop()
            path = path + [node] 

            if not getattr(node, 'children', None):
                paths.append(path)
            else:
                for child in reversed(node.children):
                    stack.append((child, path))

        return paths


    def fill_pos_nodes(self, postag, word, unary_chain, unary_joiner):
        if self.label == postag:
            # if the current level is already a postag level. This may happen on 
            # trees shaped as (NP tree) that exist on the SPMRL treebanks
            self.children.append(C_Tree(word, []))
            return
        
        if unary_chain:
            unary_chain = unary_chain.split(unary_joiner)
            unary_chain.reverse()
            pos_tree = C_Tree(postag, [C_Tree(word, [])])
            for node in unary_chain:
                temp_tree = C_Tree(node, [pos_tree])
                pos_tree = temp_tree
        else:
            pos_tree = C_Tree(postag, [C_Tree(word, [])])

        self.add_child(pos_tree)
    
    def prune_nones(self):
        '''
        Returns a new C_Tree where all the nodes with
        label -NONE- are removed. The removed nones will have their
        children added to parent
        '''
        if self.label != C_NONE_LABEL or self.label == "":
            t = C_Tree(self.label, [])
            new_childs = [c.prune_nones() for c in self.children]
            t.add_child(new_childs)
            return t
        
        else:
            return [c.prune_nones() for c in self.children]
        
    def remove_conflicts(self, conflict_strat):
        '''
        Removes all conflicts in the label of the tree generated
        during the decoding process. Conflicts will be signaled by -||- 
        string.
        '''
        for c in self.children:
            if type(c) is C_Tree:
                c.remove_conflicts(conflict_strat)
        if C_CONFLICT_SEPARATOR in self.label:
            labels = self.label.split(C_CONFLICT_SEPARATOR)
            
            if conflict_strat == C_STRAT_MAX:
                self.label = max(set(labels), key=labels.count)
            if conflict_strat == C_STRAT_FIRST:
                self.label = labels[0]
            if conflict_strat == C_STRAT_LAST:
                self.label = labels[len(labels)-1]

    def clean_binary_nodes(self, binary_marker):
        '''
        Removes binary node marks that may stay as leftovers for binary trees.
        '''
        if binary_marker in self.label:
            self.label = self.label.replace(binary_marker, "")
        for c in self.children:
            c.clean_binary_nodes(binary_marker)

    def postprocess_tree(self, conflict_strat=C_STRAT_MAX, clean_nulls=True, default_root="S", binary_marker="[b]"):
        '''
        Returns a C_Tree object with conflicts in node labels removed
        and with NULL nodes cleaned.
        '''
        if clean_nulls:
            if self.label == C_NONE_LABEL:
                self.label = default_root
            t = self.prune_nones()
        
        t.remove_conflicts(conflict_strat)
        t.clean_binary_nodes(binary_marker)
        return t
        
        # print( fix_tree)
        
    def reverse_tree(self):
        '''
        Reverses the order of all the tree children
        '''
        for c in self.children:
            if type(c) is C_Tree:
                c.reverse_tree()
        self.children.reverse()

    def shallow_equals(self, other):
        '''
        Returns true if the trees have the same label and the same number of children
        '''
        return self.label == other.label and len(self.children) == len(other.children) and all([c.shallow_equals(other.children[i]) for i,c in enumerate(self.children)])

    def update_custody(self):
        '''
        Updates the custody of all the nodes in the tree
        '''
        for c in self.children:
            c.parent = self
            if type(c) is C_Tree:
                c.update_custody()

# Printing and python-related functions
    def __str__(self):
        if len(self.children) == 0:
            label_str = self.label
            
            if self.features is not None:
                features_str = "##" + "|".join([key+"="+value for key,value in self.features.items()])
            
            label_str = label_str.replace("(","-LBR-")
            label_str = label_str.replace(")","-RBR-")
            label_str = label_str.replace(" ","-BLK-")
        else:
            label_str =  "(" + self.label + " "
            if self.features is not None:
                features_str = "##"+ "|".join([key+"="+value for key,value in self.features.items()]) 
            
            label_str += " ".join([str(child) for child in self.children]) + ")"
        return label_str

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, type(self)) and
            str(self) == str(other) and
            self.parent == other.parent
        )

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        yield self.label
        for child in self.children:
            yield child

    def __contains__(self, item):
        return item in self.label or item in self.children

    @staticmethod
    def pretty_print(tree, level=0):
        '''
        Prints the tree in a pretty format using tabs 
        according to the level of the tree. An exception will be
        the part-of-speech tags that will be printed without tabs.
        Part-of-speech tags will be the preterminal nodes of the tree.
        '''
        indent = '\t' * level

        if not tree.children:
            # Terminal node
            print(indent + tree.label)
        elif len(tree.children) == 1 and not tree.children[0].children:
            # Preterminal node (POS tag)
            print(indent + '(' + tree.label + ' ' + tree.children[0].label + ')')
        else:
            # Non-terminal node
            print(indent + '(' + tree.label)
            for child in tree.children:
                C_Tree.pretty_print(child, level + 1)
            print(indent + ')')

    @staticmethod
    def to_latex(tree):
        '''
        Returns a latex representation of the tree
        using the qtree package shaped as 

        \begin{tikzpicture}[scale=0.75]
            \Tree 
                [.S 
                    [.NP
                        [.DT The ]
                        [.NNS owls ]
                    ]
                        [.VP
                            [.VBP are ]
                            [.RB not ]
                            [.SBAR
                                [.WHNP 
                                    [.WP what ] 
                                ]
                                [.S
                                    [.NP+PRP they ] 
                                    [.VP+VBP seem ] 
                                ]
                            ]
                        ]
                        [.PUNCT . ]
                    ]            
        \end{tikzpicture}
        '''
        latex_str = "\\begin{tikzpicture}[scale=0.75]\n"
        latex_str += "\\Tree\n"
        latex_str += "\t[." + tree.label + "\n"
        latex_str += "\t\t" + " ".join([C_Tree.to_latex(child) for child in tree.children]) + "\n"
        latex_str += "\t]\n"
        latex_str += "\\end{tikzpicture}"
        print(latex_str)

# Tree creation
    @staticmethod
    def from_string(s):
        s = s.replace("(","( ")
        s = s.replace(")"," )")
        s = s.split(" ")
        
        # create dummy label and append it to the stack
        stack = []        
        i=0
        while i < (len(s)):
            if s[i]=="(":
                # If we find a l_brk we create a new tree
                # with label=next_word. Skip next_word.
                w = s[i+1]
                t = C_Tree(w, [])
                stack.append(t)
                i+=1

            elif s[i]==")":
                # If we find a r_brk set top of the stack
                # as children to the second top of the stack

                t = stack.pop()
                
                if len(stack)==0:
                    return t

                pt = stack.pop()
                pt.add_child(t)
                stack.append(pt)
            
            else:
                # If we find a word set it as children
                # of the current tree.
                t = stack.pop()
                w = s[i]
                c = C_Tree(w, [])
                t.add_child(c)
                stack.append(t)

            i+=1
        return t

    @staticmethod
    def read_trees_file(file_path):
        trees = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # fix for windows
                if line.endswith("\n"):
                    line = line[:-1]
                    
                trees.append(C_Tree.from_string(line))
        return trees

# node creation
    @staticmethod
    def make_node(lbl, lchild, rchild):
        return C_Tree(lbl, [lchild, rchild])

# tree simplification
    @staticmethod
    class TreeTransformer:
        def __init__(self):
            self.nt_counter = 1
            self.pos_counter = 1
            self.word_counter = 1
            self.nt_map = {}
            self.pos_map = {}
            self.word_map = {}
        
        def simplify_Tree(self, tree):
            nodes = []
            C_Tree.preorder(tree, lambda x: nodes.append(x))
            
            for node in nodes:
                # print(f"Processing node: {node.label:<15} is_terminal={str(node.is_terminal()):<5} \tis_preterminal={str(node.is_preterminal()):<5}")

                if node.is_terminal():
                    self.word_map[node.label] = f"w{self.word_counter}"
                    # print(f"Mapping word: {node.label} -> {self.word_map[node.label]}")
                    self.word_counter += 1
                    node.label = self.word_map[node.label]
                
                elif node.is_preterminal():
                    self.pos_map[node.label] = f"p{self.pos_counter}"
                    # print(f"Mapping postag: {node.label} -> {self.pos_map[node.label]}")
                    self.pos_counter += 1
                    node.label = self.pos_map[node.label]
                
                else:
                    self.nt_map[node.label] = f"NT{self.nt_counter}"
                    self.nt_counter += 1
                    node.label = self.nt_map[node.label]
            
            return tree
    @staticmethod
    def simplify_tree(tree):
        transformer = C_Tree.TreeTransformer()
        transformed_tree = transformer.simplify_Tree(tree)
        return transformed_tree

# Binarization
    @staticmethod
    def to_binary_left(t, binary_marker="*"):
        '''
        Converts a tree to its binary form using left binarization (iterative version).
        '''
        if not t:
            return None

        # Stack stores tuples of (current node, parent, child index in parent)
        stack = [(t, None, -1)]
        new_root = None

        while stack:
            current, parent, child_index = stack.pop()

            if len(current.children) == 0:
                # Leaf node: no changes needed
                if parent:
                    parent.children[child_index] = current
            elif len(current.children) == 1:
                # Single child: no binarization needed
                child = current.children[0]
                stack.append((child, current, 0))
            elif len(current.children) == 2:
                # Two children: no binarization needed
                left_child = current.children[0]
                right_child = current.children[1]
                stack.append((right_child, current, 1))
                stack.append((left_child, current, 0))
            else:
                # More than two children: perform left binarization
                last_child = current.children[-1]
                rest_label = (
                    current.label + binary_marker
                    if not current.label.endswith(binary_marker)
                    else current.label
                )
                rest_children = C_Tree(rest_label, current.children[:-1])
                stack.append((last_child, current, 1))  # Process last_child next
                stack.append((rest_children, current, 0))  # Process rest_children first

                # Update the current node to have only two children
                current.children = [rest_children, last_child]
                # update parent
                for c in current.children:
                    c.parent=current

            # Track the new root of the tree
            if not parent:
                new_root = current

        return new_root
        
    @staticmethod
    def to_binary_right(t, binary_marker="*"):
        '''
        Converts a tree to its binary form using right binarization.
        '''
        if not t:
            return None

        # tuples of (current node, parent, child index in parent)
        stack = [(t, None, -1)]
        new_root = None

        while stack:
            current, parent, child_index = stack.pop()
            if len(current.children) == 0:
                if parent:
                    parent.children[child_index] = current
            
            elif len(current.children) == 1:
                child = current.children[0]
                stack.append((child, current, 0))
            
            elif len(current.children) == 2:
                left_child = current.children[0]
                right_child = current.children[1]
                stack.append((right_child, current, 1))
                stack.append((left_child, current, 0))
            
            else:
                first_child = current.children[0]
                rest_label = (
                    current.label + binary_marker
                    if not current.label.endswith(binary_marker)
                    else current.label
                )
                rest_children = C_Tree(rest_label, current.children[1:])
                stack.append((rest_children, current, 1))
                stack.append((first_child, current, 0)) 

                current.children = [first_child, rest_children]
                # update parent
                for c in current.children:
                    c.parent=current

            # Track the new root of the tree
            if not parent:
                new_root = current

        return new_root


    @staticmethod
    def restore_from_binary(bt, binary_marker="*"):
        '''
        Restores a binarized tree to its original form by removing markers and flattening nodes.
        '''
        if len(bt.children) == 0:  # Leaf node
            return bt

        restored_children = []
        for c in bt.children:
            restored_child = C_Tree.restore_from_binary(c, binary_marker)
            if binary_marker in restored_child.label:  # Flatten marker nodes
                restored_children.extend(restored_child.children)
            else:
                restored_children.append(restored_child)

        bt.children = restored_children
        return bt

# Traversals
    @staticmethod
    def preorder(node, fn):
        '''
        Given a tree and a function fn, applies fn to
        each node of the tree in preorder.

        Preorder traversal:
        1. Run on root
        2. Recurse on children from left to right
        '''
        if node == None:
            return
        
        # Run on root
        fn(node)
        # Recurse on children from left to right
        for i in range(len(node.children)):
            C_Tree.preorder(node.children[i], fn)
        return
    
    @staticmethod
    def inorder(node, fn):
        '''
        Given a tree and a function fn, applies fn to
        each node of the tree in inorder.

        Inorder traversal:
        1. Recurse on children from left to right up to the last one
        2. Run on Root
        3. Recurse on the last child
        '''
        if node is None:
            return

        # If the node is a leaf, apply fn and return
        if node.is_terminal():
            fn(node)
            return

        # Traverse children from left to right, excluding the last one
        # if the tree has only one child, process it 
        for i in range(max((len(node.children) - 1), 1)):
            C_Tree.inorder(node.children[i], fn)
        fn(node)
        if len(node.children)>1:
            C_Tree.inorder(node.children[-1], fn)

    @staticmethod
    def postorder(node, fn):
        '''
        Given a tree and a function fn, applies fn to
        each node of the tree in postorder.

        Postorder traversal:
        1. Recurse on children from left to right
        2. Run on root
        '''

        if node == None:
            return
        
        # Recurse on children from left to right
        for i in range(len(node.children)):
            C_Tree.postorder(node.children[i], fn)
        
        # Run on root
        fn(node)
        return

# Default trees
    @staticmethod
    def empty_tree():
        return C_Tree(C_NONE_LABEL, [])