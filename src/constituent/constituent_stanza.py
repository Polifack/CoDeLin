from stanza.models.constituency.parse_tree import Tree as stanzatree
from stanza.models.constituency.tree_reader import read_trees
import copy
import re

C_ABSOLUTE_ENCODING = 'ABS'
C_RELATIVE_ENCODING = 'REL'
C_DYNAMIC_ENCODING = 'DYN'

C_STRAT_FIRST="strat_first"
C_STRAT_LAST="strat_last"
C_STRAT_MAX="strat_max"

class encoded_constituent_label:
    def __init__(self, et, nc, lc):
        self.encoding_type=et
        self.n_commons=nc
        self.last_common=lc
    
    def to_absolute(self, last_label):
        self.n_commons+=last_label.n_commons
        self.encoding_type=C_ABSOLUTE_ENCODING

##############################

class constituent_encoder:
    def __init__(self, encoder):
        self.encoder = encoder

    def encode(self, tree):
        self.preprocess_tree(tree)
        pos_tags = self.get_pos_tags(tree)
        path_to_leaves = self.path_to_leaves(tree)

        labels = self.encoder.encode(tree, path_to_leaves)
        return labels, pos_tags

    def preprocess_tree(self, tree):
        tree.children=(*tree.children,stanzatree("FINISH",[]))
        self.collapse_unary(tree)

    def collapse_unary(self, tree):
        for child in tree.children:
            self.collapse_unary(child)
        if len(tree.children)==1 and not tree.is_preterminal():
                tree.label+="+"+tree.children[0].label
                tree.children=tree.children[0].children

    def get_pos_tags(self, tree):
        return self.get_pos_tags_rec(tree, [])
    def get_pos_tags_rec(self, tree,accum):
        for child in tree.children:
            self.get_pos_tags_rec(child,accum)
        if len(tree.children)==1 and tree.is_preterminal():
            accum.append((tree.children[0].label,tree.label))
        return accum

    def path_to_leaves(self, tree):
        return self.path_to_leaves_rec(tree,[],[],0)
    def path_to_leaves_rec(self, tree, current_path, paths, idx):
        path_i=[]
        if (len(tree.children)==0):
            for element in current_path:
                path_i.append(element)
            path_i.append(tree.label)
            paths.append(path_i)
        else:
            common_path=copy.deepcopy(current_path)
            common_path.append(tree.label+str(idx))
            for child in tree.children:
                self.path_to_leaves_rec(child, common_path, paths,idx)
                idx+=1
        return paths

class c_relative_encoder:
    def encode(self, tree, ptl):
        labels=[]
        last_n_common=0
        for i in range(0, len(ptl)-1):
            path_n_0=ptl[i]
            path_n_1=ptl[i+1]
            
            last_common=""
            n_commons=0
            for a,b in zip(path_n_0, path_n_1):
                # if we have an ancestor that is not common break
                if (a!=b):
                    last_common=re.sub(r'[0-9]+', '', last_common)
                    lbl=encoded_constituent_label(C_RELATIVE_ENCODING,n_commons-last_n_common,last_common)
                    last_n_common=n_commons
                    labels.append(lbl)
                    break
                
                # increase
                n_commons+=1+(len(a.split("+"))-1)            
                last_common = a
        return labels
class c_absolute_encoder:
    def encode(self, tree, ptl):
        labels=[]
        for i in range(0, len(ptl)-1):
            path_n_0=ptl[i]
            path_n_1=ptl[i+1]
            
            last_common=""
            n_commons=0
            for a,b in zip(path_n_0, path_n_1):
                # if we have an ancestor that is not common break
                if (a!=b):
                    last_common=re.sub(r'[0-9]+', '', last_common)
                    lbl=encoded_constituent_label(C_ABSOLUTE_ENCODING,n_commons,last_common)
                    labels.append(lbl)
                    break
                
                # increase
                n_commons+=1+(len(a.split("+"))-1)            
                last_common = a
        return labels
class c_dynamic_encoder:
    def encode(self, tree, path_to_leaves):
        labels=[]
        last_n_common=0
        
        # encoding as labels (most_deep_common_ancestor, n_common_ancestors)
        for i in range(0, len(path_to_leaves)-1):
            path_n_0=path_to_leaves[i]
            path_n_1=path_to_leaves[i+1]
            
            last_common=""
            n_commons=0            
            for a,b in zip(path_n_0, path_n_1):
                # if we have an ancestor that is not common break
                if (a!=b):
                    abs_val = n_commons
                    rel_val = (n_commons-last_n_common)
                    last_common=re.sub(r'[0-9]+', '', last_common)
                    
                    # abs_val <= 3 : the node n-1 and n share at most 3 levels
                    # rel_val <=-2 : the node n-1 is at least 2 levels deeper than node n
                    if (abs_val<=3 and rel_val<=-2):
                        lbl = encoded_constituent_label(C_ABSOLUTE_ENCODING, abs_val, last_common)
                    else:
                        lbl=encoded_constituent_label(C_RELATIVE_ENCODING,rel_val,last_common)

                    labels.append(lbl)
                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=(len(a.split("+"))-1)
                n_commons+=1
                
                last_common = a
        
        return labels

##############################

class constituent_decoder:
    def __init__(self, decoder):
        self.decoder = decoder

    def preprocess_label(self, label):
        #  split the unary chains
        label.last_common=label.last_common.split("+")

    def fill_pos_nodes(self, current_level, pos_tags):
        word = pos_tags[0]
        pos_chain=pos_tags[1].split("+")
        
        # if the postag has only the word and the postag
        if len(pos_chain)==1:
            pos_tree=stanzatree(pos_tags[1], stanzatree(word))

        # if the postag has previous nodes
        else:
            pos_chain.reverse()
            pos_tree = stanzatree(pos_chain[0], stanzatree(word))
            pos_chain = pos_chain[1:]
            for pos_node in pos_chain:
                temp_tree=stanzatree(pos_node, pos_tree)
                pos_tree=temp_tree

        current_level.children=(*current_level.children,pos_tree)

    def decode(self, labels, pos_tags):
        return self.decoder.decode(labels, pos_tags, self.preprocess_label, self.fill_pos_nodes)

class c_absolute_decoder:
    def decode(self, labels, pos_tags, preprocess_label, fill_pos_nodes):
        tree = stanzatree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label,pos_tag in zip(labels,pos_tags):
            # preprocess the label
            preprocess_label(label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='NULL'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels): 
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='NULL'):
                        current_level.label=label.last_common[i]
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                fill_pos_nodes(current_level,pos_tag)
            else:
                fill_pos_nodes(old_level,pos_tag)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
        
        # remove dummy root node
        tree=tree.children[0]
        return tree
class c_relative_decoder:
    def decode(self, labels, pos_tags, preprocess_label, fill_pos_nodes):
        tree = stanzatree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label,pos_tag in zip(labels,pos_tags):
            # preprocess the label
            preprocess_label(label)
            if last_label!=None:
                label.to_absolute(last_label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='NULL'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels): 
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='NULL'):
                        current_level.label=label.last_common[i]
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                fill_pos_nodes(current_level,pos_tag)
            else:
                fill_pos_nodes(old_level,pos_tag)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
            last_label=label
        
        # remove dummy root node
        tree=tree.children[0]
        return tree
class c_dynamic_decoder:
    def decode(self, labels, pos_tags, preprocess_label, fill_pos_nodes):
        tree = stanzatree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label,pos_tag in zip(labels,pos_tags):
            # preprocess the label
            preprocess_label(label)
            if last_label!=None and label.encoding_type==C_RELATIVE_ENCODING:
                label.to_absolute(last_label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='NULL'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('NULL',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels): 
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='NULL'):
                        current_level.label=label.last_common[i]
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                fill_pos_nodes(current_level,pos_tag)
            else:
                fill_pos_nodes(old_level,pos_tag)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
            last_label=label
        
        # remove dummy root node
        tree=tree.children[0]
        return tree


def test_single(txt,e,d):
    tree=read_trees(txt)[0]
    
    original_tree = copy.deepcopy(tree)
    
    labels, pos_tags = e.encode(tree)
    decoded_tree=d.decode(labels,pos_tags)
    
    return (decoded_tree==original_tree)

def test_file(filepath,e,d):
    f=open(filepath)
    i=0
    for line in f:
        r=test_single(line,e,d)
        print(r)
        i+=1

if __name__=="__main__":
    e = constituent_encoder(c_absolute_encoder())
    d = constituent_decoder(c_absolute_decoder())
    test_file("./test/constituency/train.trees",e,d)