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

# Getters
    def r_child(self):
        '''
        Function that returns the rightmost child of a tree
        '''
        return self.children[len(self.children)-1] if len(self.children)>0 else None
    
    def l_child(self):
        '''
        Function that returns the leftmost child of a tree
        '''
        return self.children[0]

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
        Function that returns the terminal nodes of a tree
        '''
        if self.is_preterminal():
            return [self]
        else:
            return [node for child in self.children for node in child.get_preterminals()]

    def get_words(self):
        '''
        Function that returns the terminal nodes of a tree
        '''
        if self.is_terminal():
            return [self.label]
        else:
            return [node for child in self.children for node in child.get_words()]

    def get_postags(self):
        '''
        Function that returns the preterminal nodes of a tree
        '''
        if self.is_preterminal():
            return [self.label]
        else:
            return [node for child in self.children for node in child.get_postags()]

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
            if node.is_terminal() or node.is_root():
                continue
            else:
                branching.append(len(node.children))
        
        return sum(branching)/len(branching) if len(branching) > 0 else 0
    
    def branching(self):
        '''
        Cmpute the 
        branching of a tree as the number of non-terminal nodes that are 
        either left or right child of their parent.
        '''

        nodes = []
        C_Tree.inorder(self, lambda x: nodes.append(x))

        branching = []
        for node in nodes:
            if node.is_terminal() or node.is_root():
                continue
            else:
                branching.append("L" if node.is_left_child() else "R")
        
        bl = branching.count("L")
        br = branching.count("R")
        
        bl_percentage = bl/(bl+br)*100 if bl+br > 0 else 0
        br_percentage = br/(bl+br)*100 if bl+br > 0 else 0
        return {"L": bl_percentage, "R": br_percentage}
    
# Checkers
    def is_right_child(self):
        '''
        Returns if a given subtree is the 
        rightmost child of its parent
        '''
        return self.parent is not None and len(self.parent.children)>1 and self.parent.children.index(self)==len(self.parent.children)-1

    def is_left_child(self):
        '''
        Returns if a given subtree is the
        leftmost child of its parent
        '''
        return self.parent is None or self.parent.children.index(self)==0
    
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

    def is_unary_chain(self):
        # Returns true if the tree is an intermediate unary chain
        if len(self.children)==1 and not (self.is_preterminal() or self.is_terminal()):
            return True
        else:
            return False

# Tree processing
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
        Removes the index markers from the tree
        '''
        if idx_marker in self.label:
            self.label = self.label.split(idx_marker)[0]

        for child in self.children:
            child.clean_tree(idx_marker)

    def collapse_unary(self, unary_joiner="+"):
        '''
        Returns a new tree where the intermediate unary chains are replaced
        by a new node where the label is formed by all the 
        members in the unary chain separated by 'unary_joiner' string.
        '''
        if self.is_unary_chain():
            c = self.children[0]
            label = c.label
            
            # get all unary chain nodes
            while c.is_unary_chain() and not c.is_preterminal():
                label += unary_joiner + c.children[0].label
                c = c.children[0]

            label = self.label + unary_joiner + label
            children = c.children
            return C_Tree(label, [c.collapse_unary(unary_joiner) for c in children])
        else:
            return C_Tree(self.label, [c.collapse_unary(unary_joiner) for c in self.children])

    def uncollapse_unary(self, unary_joiner="+"):
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

    def inherit_tree(self):
        '''
        Removes the top node of the tree and delegates it
        to its firstborn child. 
        
        (S (NP (NNP John)) (VP (VBD died))) => (NP (NNP John))
        '''
        if len(self.children)>1:
            # in this situation we cant inherit
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
        Function that adds a dummy start node to the leftmost
        part of the tree
        '''
        self.add_left_child(C_Tree(C_START_LABEL, []))
                    
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

    def postprocess_tree(self, conflict_strat=C_STRAT_MAX, clean_nulls=True, default_root="S"):
        '''
        Returns a C_Tree object with conflicts in node labels removed
        and with NULL nodes cleaned.
        '''
        if clean_nulls:
            if self.label == C_NONE_LABEL:
                self.label = default_root
            t = self.prune_nones()
        
        t.remove_conflicts(conflict_strat)
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
            
            label_str = label_str.replace("(","-LRB-")
            label_str = label_str.replace(")","-RRB-")
            label_str = label_str.replace(" ","-BLK-")
        else:
            label_str =  "(" + self.label + " "
            if self.features is not None:
                features_str = "##"+ "|".join([key+"="+value for key,value in self.features.items()]) 
            
            label_str += " ".join([str(child) for child in self.children]) + ")"
        return label_str

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash((self.label, tuple(self.children)))

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        yield self.label
        for child in self.children:
            yield child

    def __contains__(self, item):
        return item in self.label or item in self.children

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

        pass

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

# Transformation
    @staticmethod
    def make_node(lbl, lchild, rchild):
        return C_Tree(lbl, [lchild, rchild])

# Binarization
    @staticmethod
    def to_binary_left(t, binary_marker="*"):
        '''
        Given a Constituent Tree returns its
        binary form.
        '''
        if len(t.children) == 1 or len(t.children) == 0:
            return t
        if len(t.children) == 2:
            lc = C_Tree.to_binary_left(t.children[0], binary_marker)
            rc = C_Tree.to_binary_left(t.children[1], binary_marker)
            return C_Tree(t.label, [lc,rc])
        else:
            if binary_marker not in t.label:
                c1_label=t.label+binary_marker
            else:
                c1_label=t.label
            c1 = C_Tree(c1_label, t.children[:-1])
            c1 = C_Tree.to_binary_left(c1, binary_marker)
            c2 = t.children[-1]
            if type(c2) is C_Tree:
                c2 = C_Tree.to_binary_left(c2, binary_marker)
            return C_Tree(t.label, [c1, c2])
        
    @staticmethod
    def to_binary_right(t, binary_marker="*"):
        '''
        Given a Constituent Tree returns its
        binary form.
        '''
        if len(t.children) == 1 or len(t.children) == 0:
            return t
        if len(t.children) == 2:
            lc = C_Tree.to_binary_right(t.children[0], binary_marker)
            rc = C_Tree.to_binary_right(t.children[1], binary_marker)
            return C_Tree(t.label, [lc,rc])
        else:
            c1 = t.children[0]
            if type(c1) is C_Tree:
                c1 = C_Tree.to_binary_right(c1, binary_marker)

            # add the binary marker to the label            
            if binary_marker not in t.label:
                c2_label = t.label+binary_marker
            else:
                c2_label = t.label

            c2 = C_Tree(c2_label, t.children[1:])
            c2 = C_Tree.to_binary_right(c2, binary_marker)
            return C_Tree(t.label, [c1, c2])          

    @staticmethod
    def restore_from_binary(bt, binary_marker="*"):
        '''
        Given a binarized Constituent Tree returns it to
        its original form
        '''
        for c in bt.children:
            if type(bt) is C_Tree:
                c = C_Tree.restore_from_binary(c, binary_marker)
        
        new_children = []
        for c in bt.children:
            if binary_marker in c.label:
                for cc in c.children:
                    new_children.append(cc)
            else:
                new_children.append(c)
        
        bt.children = new_children
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
        2. Run in Root
        3. Run in last one
        '''
        if node == None:
            return

        # If leaf, run in root
        if len(node.children) == 0:
            fn(node)
            return

        # Run in children from left to right up to the last one
        for i in range(len(node.children)-1):
            C_Tree.inorder(node.children[i], fn)
        
        # Run in Root
        fn(node)

        # Run in last one
        C_Tree.inorder(node.children[len(node.children)-1], fn)

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