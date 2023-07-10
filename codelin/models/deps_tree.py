from codelin.utils.constants import D_ROOT_HEAD, D_NULLHEAD, D_ROOT_REL, D_POSROOT, D_EMPTYREL, D_2P_GREED, D_2P_PROP
from codelin.models.const_tree import C_Tree


class D_Node:
    def __init__(self, wid, form, lemma=None, upos=None, xpos=None, feats=None, head=None, deprel=None, deps=None, misc=None):
        # word id
        self.id = int(wid)                      
        
        # word 
        self.form = form if form else "_"       
        # word lemma/stem
        self.lemma = lemma if lemma else "_"    
        # universal postag
        self.upos = upos if upos else "_"       
        # language_specific postag
        self.xpos = xpos if xpos else "_"       
        # morphological features
        self.feats = self.parse_feats(feats) if feats else "_"    
        
        # head of the current word
        head = 0 if head is None else head
        self.head = int(head) if type(head) == str else head
        
        # type of relation with head
        self.relation = deprel                  
        # enhanced dependency graph
        self.deps = deps if deps else "_"       
        # miscelaneous data
        self.misc = misc if misc else "_"       
    
    def is_left_arc(self):
        return self.head > self.id

    def delta_head(self):
        return self.head - self.id
    
    def parse_feats(self, feats):
        if feats == '_':
            return [None]
        else:
            return [x for x in feats.split('|')]
        
    def feats_to_str(self):
        if self.feats != [None]:
            return '|'.join(self.feats)
        else:
            return '_'
        

    def check_cross(self, other):
        if ((self.head == other.head) or (self.head==other.id)):
                return False

        r_id_inside = (other.head < self.id < other.id)
        l_id_inside = (other.id < self.id < other.head)

        id_inside = r_id_inside or l_id_inside

        r_head_inside = (other.head < self.head < other.id)
        l_head_inside = (other.id < self.head < other.head)

        head_inside = r_head_inside or l_head_inside

        return head_inside^id_inside
    
    def __repr__(self):
        node_fields = self.__dict__
        node_fields['feats'] = self.feats_to_str()
        return '\t'.join(str(e) for e in list(node_fields.values()))+'\n'

    def __eq__(self, other):
        return self.__dict__ == other.__dict__    

    @staticmethod
    def from_string(conll_str):
        wid,form,lemma,upos,xpos,feats,head,deprel,deps,misc = conll_str.split('\t')
        return D_Node(int(wid), form, lemma, upos, xpos, feats, int(head), deprel, deps, misc)

    @staticmethod
    def dummy_root():
        return D_Node(0, D_POSROOT, None, D_POSROOT, None, None, 0, D_EMPTYREL, None, None)
    
    @staticmethod
    def empty_node():
        return D_Node(0, None, None, None, None, None, 0, None, None, None)

class D_Tree:
    def __init__(self, nodes: list):
        self.nodes = nodes

# getters    
    def get_node(self, id):
        return self.nodes[id-1]

    def get_edges(self):
        '''
        Return sentence dependency edges as a tuple 
        shaped as ((d,h),r) where d is the dependant of the relation,
        h the head of the relation and r the relationship type
        '''
        return list(map((lambda x :((x.id, x.head), x.relation)), self.nodes))
    
    def get_arcs(self):
        '''
        Return sentence dependency edges as a tuple 
        shaped as (d,h) where d is the dependant of the relation,
        and h the head of the relation.
        '''
        return list(map((lambda x :(x.id, x.head)), self.nodes))

    def get_relations(self):
        '''
        Return a list of relationships betwee nodes
        '''
        return list(map((lambda x :x.relation), self.nodes))
    
    def get_sentence(self):
        '''
        Return the sentence as a string
        '''
        return " ".join(list(map((lambda x :x.form), self.nodes)))

    def get_words(self):
        '''
        Returns the words of the sentence as a list
        '''
        return list(map((lambda x :x.form), self.nodes))

    def get_root(self):
        '''
        Returns the root of the tree
        '''
        for node in self.nodes:
            if node.head == 0:
                return node

    def get_indexes(self):
        '''
        Returns a list of integers representing the words of the 
        dependency tree
        '''
        return list(map((lambda x :x.id), self.nodes))

    def get_postags(self):
        '''
        Returns the part of speech tags of the tree
        '''
        return list(map((lambda x :x.upos), self.nodes))

    def get_lemmas(self):
        '''
        Returns the lemmas of the tree
        '''
        return list(map((lambda x :x.lemma), self.nodes))

    def get_heads(self):
        '''
        Returns the heads of the tree
        '''
        return list(map((lambda x :x.head), self.nodes))
    
    def get_feats(self):
        '''
        Returns the morphological features of the tree
        '''
        return list(map((lambda x :x.feats), self.nodes))

    def get_dependants(self, head):
        '''
        Returns two lists of the dependants of the given head,
        one with the dependants to the left of the head
        and one to the right
        '''
        dependants =  list(filter((lambda x :x.head == head and x.id!=head), self.nodes))
        dependants_left = list(filter((lambda x :x.id < head), dependants))
        dependants_right = list(filter((lambda x :x.id > head), dependants))
        return dependants_left, dependants_right

# update functions
    def append_node(self, node):
        '''
        Append a node to the tree and sorts the nodes by id
        '''
        self.nodes.append(node)
        self.nodes.sort(key=lambda x: x.id)

    def update_head(self, node_id, head_value):
        '''
        Update the head of a node indicated by its id
        '''
        for node in self.nodes:
            if node.id == node_id:
                node.head = head_value
                break
    
    def update_relation(self, node_id, relation_value):
        '''
        Update the relation of a node indicated by its id
        '''
        for node in self.nodes:
            if node.id == node_id:
                node.relation = relation_value
                break
    
    def update_word(self, node_id, word):
        '''
        Update the word of a node indicated by its id
        '''
        for node in self.nodes:
            if node.id == node_id:
                node.form = word
                break

    def update_upos(self, node_id, postag):
        '''
        Update the upos field of a node indicated by its id
        '''
        for node in self.nodes:
            if node.id == node_id:
                node.upos = postag
                break

    def get_next_edge(self, idx_l, idx_r):
        next_arc = None
        
        if self[idx_l].head == idx_r:
            next_arc = self[idx_l]
        
        elif self[idx_r].head == idx_l:
            next_arc = self[idx_r]
        
        return next_arc

# properties functions
    def is_leftmost(self, node):
        ''' 
        Returns true if the given node is the 
        leftmost dependant of its head
        '''
        head = node.head
        head_dependants = [x.id for x in self.nodes if x.head == head]
        head_dependants.sort()
        return head_dependants[0] == node.id
    
    def is_rightmost(self, node):
        ''' 
        Returns true if the given node is the 
        rightmost dependant of its head
        '''
        head = node.head
        head_dependants = [x.id for x in self.nodes if x.head == head]
        head_dependants.sort()
        return head_dependants[-1] == node.id
        
    def is_projective(self):
        '''
        Returns a boolean indicating if the dependency tree
        is projective (i.e. no edges are crossing). The main difference
        between projective trees and planar trees is that in projective
        trees the ROOT node is ignored.
        '''
        arcs = self.get_arcs()
        # remove arc with head 0
        arcs = list(filter((lambda x :x[1]!=0), arcs))
        for (i,j) in arcs:
            for (k,l) in arcs:
                if (i,j) != (k,l) and min(i,j) < min(k,l) < max(i,j) < max(k,l):
                    return False
        return True
    
# postprocessing
    def remove_dummy(self, return_new_tree=False):
        if not self.nodes[0].form == D_POSROOT:
            return
        
        if not return_new_tree:
            self.nodes = self.nodes[1:]
        else:
            return D_Tree(self.nodes[1:])
    
    def add_dummy_root(self):
        self.nodes.insert(0, D_Node.dummy_root())

    def postprocess_tree(self, search_root_strat=D_ROOT_HEAD, allow_multi_roots=False):
        '''
        Postprocess the tree by finding the root according to the selected 
        strategy and fixing cycles and out of bounds heads
        '''
        # 1) Find the root
        root = self.root_search(search_root_strat)
        
        # 2) Fix oob heads
        self.fix_oob_heads()
        
        # 3) Fix cycles
        self.fix_cycles(root)
        
        # 4) Set all null heads to root and remove other root candidates
        for node in self.nodes:
            if node.id == root:
                continue
            if node.head == D_NULLHEAD:
                node.head = root
            if not allow_multi_roots and node.head == 0:
                node.head = root

    def root_search(self, search_root_strat):
        '''
        Search for the root of the tree using the method indicated
        '''
        root = 1 # Default root
        for node in self.nodes:    
            if search_root_strat == D_ROOT_HEAD:
                if node.head == 0:
                    root = node.id
                    break
            
            elif search_root_strat == D_ROOT_REL:
                if node.rel == 'root' or node.rel == 'ROOT':
                    root = node.id
                    break

        # Enforce root
        self.nodes[root-1].head = 0

        return root

    def fix_oob_heads(self):
        '''
        Fixes heads of the tree (if they dont exist, if they are out of bounds, etc)
        If a head is out of bounds set it to nullhead
        '''
        for node in self.nodes:
            if node.head==D_NULLHEAD:
                continue
            if int(node.head) < 0:
                node.head = D_NULLHEAD
            elif int(node.head) > len(self.nodes):
                node.head = D_NULLHEAD
    
    def fix_cycles(self, root):
        '''
        Breaks cycles in the tree by setting the head of the node to root_id
        '''
        for node in self.nodes:
            visited = []
            
            while (node.id != root) and (node.head !=D_NULLHEAD):
                if node in visited:
                    node.head = D_NULLHEAD
                else:
                    visited.append(node)
                    next_node = min(max(node.head-1, 0), len(self.nodes)-1)
                    node = self.nodes[next_node]
        
# python related functions
    def __repr__(self):
        return "".join(str(e) for e in self.nodes)+"\n"
    
    def __iter__(self):
        for n in self.nodes:
            yield n

    def __getitem__(self, key):
        return self.nodes[key]  
    
    def __len__(self):
        return self.nodes.__len__()
    
# scorers
    def las_score(self, other):
        this = self
        accum = 0
        
        if self[0].form == D_POSROOT:
            this = self.remove_dummy(return_new_tree=True)
        if other[0].form == D_POSROOT:
            other = other.remove_dummy(return_new_tree=True)
        
        if type(this) is not D_Tree or type(other) is not D_Tree:
            print("Error: ulas score is only defined for trees")
            return 0

        for i in range(len(this)):
            if this[i].form != other[i].form:
                print("Error: ulas score is not defined for trees with different words")
                print(this, other)
                return 0
            
            accum += 1 if this[i].head == other[i].head and this[i].relation == other[i].relation else 0
        return accum/len(this)
    
    def ulas_score(self, other):
        this = self
        accum = 0
        
        if self[0].form == D_POSROOT:
            this = self.remove_dummy(return_new_tree=True)
        if other[0].form == D_POSROOT:
            other = other.remove_dummy(return_new_tree=True)
        
        if type(this) is not D_Tree or type(other) is not D_Tree:
            print("Error: ulas score is only defined for trees")
            return 0

        for i in range(len(this)):
            if this[i].form != other[i].form:
                print("Error: ulas score is not defined for trees with different words")
                print(this[i].form, other[i].form)
                return 0
            
            accum += 1 if this[i].head == other[i].head else 0
        return accum/len(this)

# base tree
    @staticmethod
    def empty_tree(l=1):
        ''' 
        Creates an empty dependency tree with l nodes
        '''
        t = D_Tree([])
        for i in range(l):
            n = D_Node.empty_node()
            n.id = i
            t.append_node(n)
        return t

# reader and writter
    @staticmethod
    def from_string(conll_str, dummy_root=True, clean_contractions=True, clean_omisions=True):
        '''
        Create a ConllTree from a dependency tree conll-u string.
        '''
        data = conll_str.split('\n')
        dependency_tree_start_index = 0
        for line in data:
            if len(line)>0 and line[0]!="#":
                break
            dependency_tree_start_index+=1
        data = data[dependency_tree_start_index:]
        nodes = []
        if dummy_root:
            nodes.append(D_Node.dummy_root())
        
        for line in data:
            # check if not valid line (empty or not enough fields)
            if (len(line)<=1) or len(line.split('\t'))<10:
                continue 
            
            wid = line.split('\t')[0]

            # check if node is a comment (comments are marked with #)
            if "#" in wid:
                continue
            
            # check if node is a contraction (multiexp lines are marked with .)
            if clean_contractions and "-" in wid:    
                continue
            
            # check if node is an omited word (empty nodes are marked with .)
            if clean_omisions and "." in wid:
                continue

            conll_node = D_Node.from_string(line)
            nodes.append(conll_node)
        
        return D_Tree(nodes)
    
    @staticmethod
    def read_conllu_file(file_path, filter_projective = True):
        '''
        Read a conllu file and return a list of ConllTree objects.
        '''
        with open(file_path, 'r') as f:
            data = f.read()
        data = data.split('\n\n')
        # remove last empty line
        data = data[:-1]
        
        trees = []
        for x in data:
            t = D_Tree.from_string(x)
            if not filter_projective or t.is_projective():
                trees.append(t)
        return trees    

    @staticmethod
    def write_conllu_file(file_path, trees):
        '''
        Write a list of ConllTree objects to a conllu file.
        '''
        with open(file_path, 'w') as f:
            f.write("".join(str(e) for e in trees))

    @staticmethod
    def write_conllu(file_io, tree):
        '''
        Write a single ConllTree to a already open file.
        Includes the # text = ... line
        '''
        file_io.write("# text = "+tree.get_sentence()+"\n")
        file_io.write("".join(str(e) for e in tree)+"\n")

    @staticmethod
    def short_print(tree):
        '''
        Print a ConllTree in a short format.
        '''
        for node in tree:
            print(node.id,'\t\t', node.form,'\t\t', node.head,'\t\t', node.relation)

    @staticmethod
    def two_planar_propagate(dep_tree):
        '''
        Separates the node of a given dependency tree into two
        non-crossing planes using the propagation algorithm.
        '''
        
        def propagate(nodes, fp1, fp2, current_edge, i):
            # add the current edge to the forbidden plane opposite to the plane
            # where the node has already been added
            fpi  = None
            fp3mi= None
            if i == 1:
                fpi  = fp1
                fp3mi= fp2
            if i == 2:
                fpi  = fp2
                fp3mi= fp1
            fpi.append(current_edge)
            
            # add all nodes from the dependency graph that crosses the current edge
            # to the corresponding forbidden plane
            for node in nodes:
                if node.check_cross(current_edge):
                    if node not in fp3mi:
                        # y si es for nodes in that plane?
                        (fp1, fp2) = propagate(nodes, fp1, fp2, node, 3-i)
            return fp1, fp2
        
        p1, p2, fp1, fp2 = [], [], [], []
        for i in range(0, (len(dep_tree))):
            for j in range(i, -1, -1):
                # if the node in position 'i' has an arc with head 'j' 
                # or node in position 'j' has an arc with head 'i'
                next_arc = dep_tree.get_next_edge(i, j)
                if next_arc is None:
                    continue
                # check restrictions
                if next_arc not in fp1:
                    p1.append(next_arc)
                    fp1, fp2 = propagate(dep_tree, fp1, fp2, next_arc, 2)
                
                elif next_arc not in fp2:
                    p2.append(next_arc)
                    fp1, fp2 = propagate(dep_tree, fp1, fp2, next_arc, 1)        
        return D_Tree(p1),D_Tree(p2)
    
    @staticmethod
    def two_planar_greedy(dep_tree):
        '''
        Separates the node of a given dependency tree into two
        non-crossing planes using the greedy algorithm.
        '''

        p1, p2 = [], []
        for i in range(len(dep_tree)):
            for j in range(i, -1, -1):
                # if the node in position 'i' has an arc to 'j' 
                # or node in position 'j' has an arc to 'i'
                next_arc = dep_tree.get_next_edge(i, j)
                if next_arc is None:
                    continue

                else:
                    cross_plane_1 = False
                    cross_plane_2 = False
                    for node in p1:
                        cross_plane_1 = cross_plane_1 or next_arc.check_cross(node)
                    for node in p2:
                        cross_plane_2 = cross_plane_2 or next_arc.check_cross(node)
                    
                    if not cross_plane_1:
                        p1.append(next_arc)
                    elif not cross_plane_2:
                        p2.append(next_arc)

        # processs them separately
        return D_Tree(p1), D_Tree(p2)

    @staticmethod
    def to_latex(tree, include_col=False, planar_separate = False, planar_alg = D_2P_GREED, planar_colors = ["black", "blue"], additional_labels = None):
        '''
        Turns a ConllTree into a latex tree using
        the tikz-dependency package formated as
        \begin{dependency}
            \begin{deptext}[row sep=.25em, column sep=1.5em]
                $w_i$           \& The      \& owls     \& are      \& not      \& what         \& they     \& seem         \& .        \\
            \end{deptext}
            \depedge{3}{2}{det}
            \depedge{4}{3}{nsubj}
            \deproot{4}{root}
            \depedge{4}{5}{advmod}
            \depedge{8}{6}{obj}
            \depedge{8}{7}{nsubj}
            \depedge{4}{8}{ccomp}
            \depedge{4}{9}{punct}
        \end{dependency}
        '''
        if planar_separate:
            if planar_alg == D_2P_GREED:
                p1, p2 = D_Tree.two_planar_greedy(tree)
            elif planar_alg == D_2P_PROP:
                p1, p2 = D_Tree.two_planar_propagate(tree)

        nodes_str = ' \& '.join([node.form for node in tree.nodes])
        indexes_str = ' \& '.join([str(node.id) for node in tree.nodes])
        latex = f"\\begin{{dependency}}[theme = simple]\n"
        latex += f"\\begin{{deptext}}[row sep=.25em, column sep=1.5em]\n"
        
        if include_col:
            latex += f"$i$ \& {indexes_str} \\\\ \n"
            latex += f"$w_i$ \& {nodes_str} \\\\ \n"

            if additional_labels is not None:
                # replace \ with \\ to avoid latex errors
                fix_labels = []
                for lbl in additional_labels:
                    r_lbl = lbl.replace("\\", "\\textbackslash")
                    fix_labels.append(f"\\texttt{{{r_lbl}}}")

                lbls = ' \& '.join(fix_labels)
                latex += f"$l_i$ \& {lbls} \\\\ \n"

        else:
            latex += f"{indexes_str} \\\\ \n"
            latex += f"{nodes_str} \\\\ \n"
            if additional_labels is not None:
                fix_labels = []
                for lbl in additional_labels:
                    r_lbl = lbl.replace("\\", "\\textbackslash")
                    fix_labels.append(f"\\texttt{{{r_lbl}}}")

                lbls = ' \& '.join(fix_labels)
                latex += f"{lbls} \\\\ \n"
        
        latex += f"\\end{{deptext}}\n"
        for node in tree.nodes:
            if node.id == 0:
                continue
            if node.head != D_NULLHEAD:
                latex += "\\depedge"
                
                if planar_separate:
                    if node in p1:
                        latex += f"[edge style={{{planar_colors[0]}}}]"
                    elif node in p2:
                        latex += f"[edge style={{{planar_colors[1]}}}]"
                    else:
                        latex += f"[edge style={{green}}]"
                
                delta = 2 if include_col else 1
                latex += f"{{{node.head+delta}}}{{{node.id+delta}}}{{{node.relation}}}"
                latex += "\n"
        
        latex += f"\\end{{dependency}}\n"
        return latex
    
    @staticmethod
    def to_bht(tree):
        '''
        Converts a dependency tree into a binary head tree.
        We will consider a bht as a constituent tree.

        BHTs are a special kind of constituent trees where
        the internal nodes are labeled with an 'L' or 'R' depending
        of the position of the head in the dependency tree
        (https://arxiv.org/pdf/2306.05477.pdf)

        The tree is built using a stack and push/make_node operations.
        We start from the root and performa a DFS traversal.
        '''
        def to_bht_rec(node):
            stack.append(node)
            ld, rd = tree.get_dependants(node.id)
            for dep in ld:
                to_bht_rec(dep)
                left = stack.pop()
                right = stack.pop()
                
                if type(left) is not C_Tree:
                    left = C_Tree(str(left.id))
                if type(right) is not C_Tree:
                    right = C_Tree(str(right.id))

                stack.append(C_Tree.make_node('R', left, right))

            for dep in rd:
                to_bht_rec(dep)
                left = stack.pop()
                right = stack.pop()
                
                if type(left) is not C_Tree:
                    left = C_Tree(str(left.id))
                if type(right) is not C_Tree:
                    right = C_Tree(str(right.id))

                stack.append(C_Tree.make_node('L', left, right))

        tree_root = tree.get_root()
        stack = []
        to_bht_rec(tree_root)
        
        return stack.pop()
    
    @staticmethod
    def from_bht(bht):
        '''
        Converts a constituent tree shaped as a binary head tree back into
        a dependency tree.
        '''
        def from_bht_rec(node):
            if node.is_terminal():
                return node
            
            left  = from_bht_rec(node.children[0])
            right = from_bht_rec(node.children[1])
            if node.label == 'L':
                # L => head to the left and dependant to the right
                node_head      = int(right.label) if type(right) is C_Tree else int(right.head)
                node_dependant = int(left.label)  if type(left) is C_Tree else int(left.head)

                n = D_Node(wid=node_dependant, form="-NONE-", head=node_head, deprel="-NONE-") 
                nodes.append(n)
            else:
                # R => head to the right and dependant to the left
                node_head      = int(right.label) if type(right) is C_Tree else int(right.head)
                node_dependant = int(left.label)  if type(left) is C_Tree  else int(left.head)

                n = D_Node(wid=node_dependant, form="-NONE-", head=node_head, deprel="-NONE-")
                nodes.append(n)
                
            return n
        
        nodes=[]
        from_bht_rec(bht)
        # sort nodes by id
        nodes = sorted(nodes, key=lambda x: x.id)
        return D_Tree(nodes)
        


    # statistics extraction
    @staticmethod
    def get_projectivity_percentage(trees):
        '''
        Given a list of trees returns the % of projective trees
        '''
        proj=0
        for tree in trees:
            tree = tree.remove_dummy(return_new_tree=True)
            if tree.is_projective():
                proj += 1

        return proj/len(trees)

    @staticmethod
    def get_planarity_percentage(trees):
        '''
        Given a list of trees returns the % of trees
        that are 1-planar or 2-planar
        '''
        planar = 0
        two_planar = 0
        n_planar = 0
        for tree in trees:
            p1,p2 = D_Tree.two_planar_greedy(tree)
            if len(p2) == 0 and len(p1) != 0:
                planar += 1
            elif len(p2) != 0 and len(p1) != 0:
                two_planar += 1
            else:
                n_planar += 1
        
        return planar/len(trees), two_planar/len(trees), n_planar/len(trees)

    @staticmethod
    def get_dependency_direction_percentage(trees):
        '''
        Given a list of trees returns the % of dependencies
        that are 'towards the right' (head > dependent)
        and the % of dependencies that are 'towards the left'
        (head < dependent)
        '''
        right = 0
        left = 0
        total = 0
        for tree in trees:
            for node in tree.nodes:
                if node.id == 0:
                    continue
                if node.head > node.id:
                    right += 1
                else:
                    left += 1
                total += 1

        return right/total, left/total
    
    @staticmethod
    def get_avg_dependants(trees):
        '''
        Given a list of trees returns the average number
        of dependants per head
        '''
        avgs=[]
        for tree in trees:
            tree_dependants = {}
            for node in tree.nodes:
                tree_dependants[node.head] = tree_dependants.get(node.head, 0) + 1
            avgs.append(sum(tree_dependants.values())/len(tree_dependants))        
        return sum(avgs)/len(avgs)
        
