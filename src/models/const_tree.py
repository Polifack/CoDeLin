from src.utils.constants import C_END_LABEL, C_START_LABEL, C_NONE_LABEL, C_DUMMY_END, C_DUMMY_START
from src.utils.constants import C_CONFLICT_SEPARATOR, C_STRAT_MAX, C_STRAT_FIRST, C_STRAT_LAST, C_NONE_LABEL
import copy

class ConstituentTree:
    def __init__(self, label, children):
        self.parent = None
        self.label = label
        self.children = children
        self.features = {}

# Adders and deleters
    def add_child(self, child):
        '''
        Function that adds a child to the current tree
        '''
        if type(child) is not ConstituentTree:
            raise TypeError("[!] Child must be a ConstituentTree")

        self.children.append(child)
        child.parent = self

    def add_left_child(self, child):
        '''
        Function that adds a child to the left of the current tree
        '''
        if type(child) is not ConstituentTree:
            raise TypeError("[!] Child must be a ConstituentTree")
        
        self.children = [child] + self.children
        child.parent = self

    def del_child(self, child):
        '''
        Function that deletes a child from the current tree
        without adding its children to the current tree
        '''
        if type(child) is not ConstituentTree:
            raise TypeError("[!] Child must be a ConstituentTree")

        self.children.remove(child)
        child.parent = None

# Getters
    def r_child(self):
        '''
        Function that returns the rightmost child of a tree
        '''
        return self.children[len(self.children)-1]
    
    def l_child(self):
        '''
        Function that returns the leftmost child of a tree
        '''
        return self.children[0]

    def r_siblings(self):
        '''
        Function that returns the right siblings of a tree
        '''
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

# Word and Postags getters
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

# Terminal checking
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

# Terminal getters
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

# Tree processing
    def collapse_unary(self, unary_joiner="+"):
        '''
        Function that collapses unary chains
        into single nodes using a unary_joiner as join character
        '''
        for child in self.children:
            child.collapse_unary(unary_joiner)
        if len(self.children)==1 and not self.is_preterminal():
            self.label += unary_joiner + self.children[0].label
            self.children = self.children[0].children

    def add_end_node(self):
        '''
        Function that adds a dummy end node to the 
        rightmost part of the tree
        '''
        self.add_child(ConstituentTree(C_END_LABEL, []))

    def add_start_node(self):
        '''
        Function that adds a dummy start node to the leftmost
        part of the tree
        '''
        self.add_left_child(ConstituentTree(C_START_LABEL, []))
        

    def path_to_leaves(self, collapse_unary=True, unary_joiner="+", dummy=C_DUMMY_END):
        '''
        Function that given a Tree returns a list of paths
        from the root to the leaves, encoding a level index into
        nodes to make them unique.
        '''
            
        if collapse_unary:
            self.collapse_unary(unary_joiner)

        if dummy==C_DUMMY_END:
            self.add_end_node()
            return self.path_to_leaves_rec_end([],[],0)
        
        elif dummy==C_DUMMY_START:
            self.add_start_node()
            return self.path_to_leaves_rec_start([],[],0)
        else:
            raise ValueError("[!] Dummy must be either C_DUMMY_END or C_DUMMY_START")


    def path_to_leaves_rec_end(self, current_path, paths, idx):
        '''
        Recursive step of the path_to_leaves function where we store
        the common path based on the current node
        '''

        if (len(self.children) == 0):
            current_path.append(self.label)
            paths.append(current_path)
        
        else:
            common_path = copy.deepcopy(current_path)
            common_path.append(self.label+str(idx)) 
            for child in self.children:                
                child.path_to_leaves_rec_end(common_path, paths, idx)
                idx+=1
        
        return paths

    def path_to_leaves_rec_start(self, current_path, paths, idx):
        '''
        Recursive step of the path_to_leaves function where we store the 
        common path based on the previous node
        '''

        if (len(self.children) == 0):
            current_path.append(self.label)
            paths.append(current_path)
        
        else:
            for child in self.children:                
                common_path = copy.deepcopy(current_path)
                common_path.append(self.label+str(idx)) 
                child.path_to_leaves_rec_start(common_path, paths, idx)
                idx+=1
        
        return paths


    def extract_features(self, f_mark = "##", f_sep = "|"):
        # go through all pre-terminal nodes
        # of the tree
        for node in self.get_preterminals():
            if f_mark in node.label:
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


    def fill_pos_nodes(self, postag, word, unary_chain, unary_joiner):
        if unary_chain:
            unary_chain = unary_chain.split(unary_joiner)
            unary_chain.reverse()
            pos_tree = ConstituentTree(postag, [ConstituentTree(word, [])])
            for node in unary_chain:
                temp_tree = ConstituentTree(node, [pos_tree])
                pos_tree = temp_tree
        else:
            pos_tree = ConstituentTree(postag, [ConstituentTree(word, [])])

        self.add_child(pos_tree)

    def renounce_children(self):
        '''
        Function that deletes current tree from its parent
        and adds its children to the parent
        '''
        self.parent.children = self.l_siblings() + self.children + self.r_siblings()
        for child in self.children:
            child.parent = self.parent
 
    def postprocess_tree(self, conflict_strat, clean_nulls=True, default_root="S"):
        '''
        Apply heuristics to the reconstructed Constituent Trees
        in order to ensure correctness
        '''
        
        # Postprocess Childs
        for c in self.children:
            if type(c) is ConstituentTree:
                c.postprocess_tree(conflict_strat, clean_nulls)

        if (clean_nulls):
            # Clean Null Labels
            if self.label == C_NONE_LABEL:
                # Null label in children
                if self.parent is not None:
                    self.renounce_children()
                # Null label in root
                else:
                    self.label = default_root

        # Clean conflicts
        if C_CONFLICT_SEPARATOR in self.label:
            labels = self.label.split(C_CONFLICT_SEPARATOR)
            
            if conflict_strat == C_STRAT_MAX:
                self.label = max(set(labels), key=labels.count)
            if conflict_strat == C_STRAT_FIRST:
                self.label = labels[0]
            if conflict_strat == C_STRAT_LAST:
                self.label = labels[len(labels)-1]

# Printing and python-related functions
    def __str__(self):
        if len(self.children) == 0:
            label_str = self.label
            label_str = label_str.replace("(","-LRB-")
            label_str = label_str.replace(")","-RRB-")
            return label_str
        else:
            return "(" + self.label + " " + " ".join([str(child) for child in self.children]) + ")"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, ConstituentTree):
            return self.label == other.label and self.children == other.children
        return False

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
                t = ConstituentTree(w, [])
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
                c = ConstituentTree(w, [])
                t.add_child(c)
                stack.append(t)

            i+=1
        return t

# Default trees
    @staticmethod
    def empty_tree():
        return ConstituentTree(C_NONE_LABEL, [])