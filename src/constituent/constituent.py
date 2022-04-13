from nltk.tree import Tree, ParentedTree
import copy
import re

C_ABSOLUTE_ENCODING = 'ABS'
C_RELATIVE_ENCODING = 'REL'
C_DYNAMIC_ENCODING = 'DYN'

class encoded_constituent_label:
    # labels obtained during the encoding of constituent trees
    # nc: number of common ancestors
    # lc: last common
    # et: encoding type
    def __init__(self, et, nc, lc):
        self.encoding_type=et
        self.n_commons=nc
        self.last_common=lc

##############################################################################
##############################################################################
##############################################################################

class constituent_encoder:
    def __init__(self, encoding_type):
        self.encoder = encoding_type
    
    def preprocess_tree(self, tree):
        # append dummy finish node
        tree.append(Tree("FINISH",["finish"]))

    def encode(self, tree):
        return self.encoder.encode(tree)

class constituent_naive_encoder:
    def get_pos_tags(self, tree):
        # if we have a tree with only one child
        if (len(tree)==1):
            collapsed=[]
            while type(tree) is Tree:
                collapsed.append(tree.label())
                tree=tree[-1]
            # in the tree now remains only the word
            word=tree
            return (word, collapsed)

        else:
            return tree.pos()

    # returns array of leave paths
    def get_path_to_leaves(self, tree):
        ptl=self.get_path_to_leaves_rec([tree], [],[])
        return ptl

    def get_path_to_leaves_rec(self, tree, current_path, paths):
        for i, child in enumerate(tree):
            pathi = []
            if type(child) is Tree:
                common_path = copy.deepcopy(current_path)
                label = child.label()

                common_path.append(label+str(i))
                self.get_path_to_leaves_rec(child, common_path, paths)
            else:
                for element in current_path:
                    pathi.append(element)
                pathi.append(child)
                paths.append(pathi)
        return paths

class constituent_absolute_encoder(constituent_naive_encoder):
    def encode(self, tree):
        path_to_leaves = self.get_path_to_leaves(tree)
        labels=[]

        # encoding as labels (most_deep_common_ancestor, n_common_ancestors)

        for i in range(0, len(path_to_leaves)-1):
            path_n_0=path_to_leaves[i][:-1]
            path_n_1=path_to_leaves[i+1][:-1]
            
            last_common=""
            n_commons=0
            for a,b in zip(path_n_0, path_n_1):
                # if we have an ancestor that is not common break
                if (a!=b):
                    lbl=encoded_constituent_label(C_ABSOLUTE_ENCODING,n_commons,last_common)
                    labels.append(lbl)
                    break
                
                # increase
                n_commons+=(len(a.split("+"))-1)
                n_commons+=1
                
                last_common = a
        return labels

class constituent_relative_encoder(constituent_naive_encoder):
    def encode(self, tree):
        path_to_leaves = self.get_path_to_leaves(tree)
        labels=[]

        last_n_common=0
        
        # encoding as labels (most_deep_common_ancestor, n_common_ancestors)
        for i in range(0, len(path_to_leaves)-1):
            path_n_0=path_to_leaves[i][:-1]
            path_n_1=path_to_leaves[i+1][:-1]
            
            last_common=""
            n_commons=0            
            for a,b in zip(path_n_0, path_n_1):
                # if we have an ancestor that is not common break
                if (a!=b):
                    lbl=encoded_constituent_label(C_RELATIVE_ENCODING,(n_commons-last_n_common),last_common)
                    labels.append(lbl)
                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=(len(a.split("+"))-1)
                n_commons+=1
                
                last_common = a
        
        return labels

##############################################################################
##############################################################################
##############################################################################

class constituent_decoder:
    def __init__(self, decoding_type):
        self.decoder = decoding_type
    
    def decode(self, labels, pos_tags):
        return self.decoder.decode(labels, pos_tags)

class constituent_absolute_decoder:
    def __init__(self):
        pass
    
    def preprocess_label(self,label):
        # clean the int added during encoding
        label.last_common=re.sub(r'[0-9]+', '', label.last_common)

        #  split the unary chains
        label.last_common=label.last_common.split("+")


    def fill_intermediate_node(self, current_level, last_commons):
        if len(last_commons)==1:
            if (current_level.label()=='NULL'):
                current_level.set_label(last_commons[0])
        else:
            last_commons.reverse()
            for element in last_commons:
                current_level.set_label(element)
                current_level=current_level.parent()

    def fill_pos_nodes(self, current_level, pos_tags):
        word = pos_tags[0]
        pos_chain=pos_tags[1].split("+")
        
        # if the postag has only the word and the postag
        if len(pos_chain)==1:
            pos_tree=ParentedTree(pos_tags[1], [word])

        # if the postag has previous nodes
        else:
            pos_chain.reverse()
            pos_tree = ParentedTree(pos_chain[0], [word])
            pos_chain=pos_chain[1:]
            for pos_node in pos_chain:
                temp_tree=ParentedTree(pos_node,[pos_tree])
                pos_tree=temp_tree



        #pos_tree=ParentedTree(pos_tags[1], [pos_tags[0]])
        current_level.append(pos_tree)

    def decode(self, labels, pos_tags):
        tree = ParentedTree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True

        for label,pos_tag in zip(labels,pos_tags):
            # preprocess the label
            self.preprocess_label(label)

            # reset current_level to the head of the tree
            current_level = tree

            # descend n_commons levels
            for level_index in range(label.n_commons): 
                # if the current level has no childs or
                # if we are in a level deeper than the previous label level
                # insert an empty node
                if (len(current_level)==0) or (level_index >= old_n_commons):
                    current_level.append(ParentedTree("NULL",[]))
                current_level = current_level[-1]
            
            # dealing with intermediate labels
            self.fill_intermediate_node(current_level, label.last_common)           

            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                self.fill_pos_nodes(current_level,pos_tag)
            else:
                self.fill_pos_nodes(old_level,pos_tag)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
        
        # remove dummy root node
        tree=tree[-1]

        return tree

class constituent_relative_decoder:
    def __init__(self):
        pass
    
    def preprocess_label(self,label):
        # clean the int added during encoding
        label.last_common=re.sub(r'[0-9]+', '', label.last_common)

        #  split the unary chains
        label.last_common=label.last_common.split("+")

    def fill_intermediate_node(self, current_level, last_commons):
        if len(last_commons)==1:
            if (current_level.label()=='NULL'):
                current_level.set_label(last_commons[0])
        else:
            last_commons.reverse()
            for element in last_commons:
                current_level.set_label(element)
                current_level=current_level.parent()

    def fill_pos_nodes(self, current_level, pos_tags):
        word = pos_tags[0]
        pos_chain=pos_tags[1].split("+")
        
        # if the postag has only the word and the postag
        if len(pos_chain)==1:
            pos_tree=ParentedTree(pos_tags[1], [word])

        # if the postag has previous nodes
        else:
            pos_chain.reverse()
            pos_tree = ParentedTree(pos_chain[0], [word])
            pos_chain=pos_chain[1:]
            for pos_node in pos_chain:
                temp_tree=ParentedTree(pos_node,[pos_tree])
                pos_tree=temp_tree

        current_level.append(pos_tree)

    def decode(self, labels, pos_tags):
        tree = ParentedTree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        

        for label,pos_tag in zip(labels,pos_tags):
            # preprocess the label
            # this returns the delta levels to move obtained during unary chain split
            self.preprocess_label(label)
            
            if label.n_commons>0:
                for level_index in range(label.n_commons): 
                    current_level.append(ParentedTree("NULL",[]))
                    current_level = current_level[-1]
            else:
                for level_index in range(-label.n_commons):
                    current_level = current_level.parent()

            # dealing with intermediate labels
            self.fill_intermediate_node(current_level, label.last_common)           

            # dealing with PoS

            # positivo -> insert en nivel actual
            # negativo // 0 -> insert en nivel anterior

            if is_first or (label.n_commons > 0):
                is_first=False
                self.fill_pos_nodes(current_level,pos_tag)
            else:
                self.fill_pos_nodes(old_level,pos_tag)
            
            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
        
        # remove dummy root node
        tree=tree[-1]

        return tree    


def test_single(ts):
    # Get tree from string
    t = Tree.fromstring(ts)
    t.pretty_print()

    # create encoder
    re=constituent_relative_encoder()
    ae=constituent_absolute_encoder()

    e = encoder(re)

    # preprocess it
    e.preprocess_tree(t)

    # Collapse the unary nodes in the tree
    t.collapse_unary(collapsePOS=True)

    # get the postags
    pos_tags = e.encoder.get_pos_tags(t)

    # get labels
    labels = e.encode(t)

    # decode labels
    rd=constituent_relative_decoder()
    ad=constituent_absolute_decoder()

    d = constituent_decoder(rd)
    decoded_tree=d.decode(labels, pos_tags)
    decoded_tree.pretty_print()

def test_file(filepath):
    f=open(filepath)
    for line in f:
        test_single(line)
