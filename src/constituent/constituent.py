from stanza.models.constituency.parse_tree import Tree as stanzatree
from stanza.models.constituency.tree_reader import read_trees, read_tree_file
import stanza.pipeline
import copy
import re

C_ABSOLUTE_ENCODING = 'ABS'
C_RELATIVE_ENCODING = 'REL'
C_DYNAMIC_ENCODING = 'DYN'

C_STRAT_FIRST="strat_first"
C_STRAT_LAST="strat_last"
C_STRAT_MAX="strat_max"

class encoded_constituent_label:
    def __init__(self, et, nc, lc, uc):
        self.encoding_type=et
        self.n_commons=nc
        self.last_common=lc
        self.unary_chain=uc
    
    def __repr__(self):
        uchain = ""
        if self.unary_chain:
            for element in self.unary_chain:
                uchain+="+"+element
            uchain=uchain[1:]
        else:
            uchain = "-NONE-"
            
        return f'{self.n_commons}_{self.last_common}_{uchain}_{self.encoding_type}'
    
    # no longer used
    def to_absolute(self, last_label):
        self.n_commons+=last_label.n_commons
        self.encoding_type=C_ABSOLUTE_ENCODING

##############################

class constituent_encoder:
    def __init__(self, encoding, collapse_unary):
        self.encoder = ENCODINGS_MAP[encoding]['encoder']()
        self.do_collapse=collapse_unary

    def encode(self, tree):
        # add finish point to ensure all labels are encoded
        tree.children=(*tree.children,stanzatree("-END-",[stanzatree("-END-")]))

        # collapse unary 
        if self.do_collapse:
            self.collapse_unary(tree)

        # get postags, words and path_to_leaves
        words, postags = self.preprocess_tree(tree)
        path_to_leaves = self.path_to_leaves(tree)

        # encode labels
        labels = self.encoder.encode(tree, path_to_leaves)
        for l, p in zip(labels, postags):
            postags_list = p.split("+")
            if len(postags_list)>1:
                l.unary_chain=postags_list[:-1]
                postags[postags.index(p)]=postags_list[-1]

        # return with [:-1] because of dummy root
        return labels, postags, words
   
    def collapse_unary(self, tree):
        for child in tree.children:
            self.collapse_unary(child)
        if len(tree.children)==1 and not tree.is_preterminal():
                tree.label+="+"+tree.children[0].label
                tree.children=tree.children[0].children
    def preprocess_tree(self, tree):
        words = []
        postags = []
        tree.visit_preorder(preterminal=lambda e:postags.append(e.label),
                            leaf=lambda e:words.append(e.label))
        return words, postags

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
                    last_common = re.sub(r'[0-9]+', '', last_common)
                    lbl=encoded_constituent_label(C_RELATIVE_ENCODING,n_commons-last_n_common,last_common, None)
                    last_n_common=n_commons
                    labels.append(lbl)
                    break
                
                # increase
                n_commons+=len(a.split("+"))
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
                    lbl=encoded_constituent_label(C_ABSOLUTE_ENCODING,n_commons,last_common, None)
                    labels.append(lbl)
                    break
                
                # increase
                n_commons+=len(a.split("+"))
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
                        lbl = encoded_constituent_label(C_ABSOLUTE_ENCODING, abs_val, last_common, None)
                    else:
                        lbl=encoded_constituent_label(C_RELATIVE_ENCODING,rel_val,last_common, None)

                    labels.append(lbl)
                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=len(a.split("+"))
                
                last_common = a
        
        return labels

##############################

class constituent_decoder:
    def __init__(self, encoding, do_clean_nulls, conflict_strat=C_STRAT_MAX):
        self.decoder = ENCODINGS_MAP[encoding]['decoder']()
        self.conflict_strat=conflict_strat
        self.do_clean_nulls = do_clean_nulls

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

    def clean_nulls(self, tree, tree_children):
        # if during decode we find -NONE- nodes 
        # we append each of the child of those nodes to the
        # parent node

        for c in tree_children:
            if c.label == '-NONE-':
                # python tuples are immutable, so to remove them we have to create a new
                new_children = []
                none_child_idx = tree_children.index(c)
                
                # append children to the "left"
                for i in range(0, none_child_idx):
                    new_children.append(tree_children[i])

                # foreach of the children of the node that has a null label
                # append them to the parent
                for nc in c.children:
                    new_children.append(stanzatree(nc.label, nc.children))

                # append children to the "right"
                for i in range(none_child_idx, len(tree_children)-1):
                    new_children.append(tree_children[i])

                tree.children=tuple(new_children)
            # recursive step
            if type(c) is stanzatree:
                self.clean_nulls(c, c.children)

    def clean_conflicts(self, tree):
        for c in tree.children:
            if "|" in  c.label:
                labels=c.label.split("|")
                if self.conflict_strat == C_STRAT_MAX:
                    c.label=max(set(labels), key=labels.count)
                if self.conflict_strat == C_STRAT_FIRST:
                    c.label=labels[0]
                if self.conflict_strat == C_STRAT_LAST:
                    c.label=labels[len(labels)-1]
                
            if type(c) is stanzatree:
                self.clean_conflicts(c)

    def decode(self, labels, pos_tags):
        # check first label not below 0
        if labels[0].n_commons<0:
            labels[0].n_commons = 0

        decoded_tree = self.decoder.decode(labels, pos_tags, self.preprocess_label, self.fill_pos_nodes)
        
        if self.do_clean_nulls:
            self.clean_nulls(decoded_tree, decoded_tree.children)
        self.clean_conflicts(decoded_tree)
        return decoded_tree

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
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='-NONE-'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels):
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='-NONE-'):
                        current_level.label=label.last_common[i]
                    else:
                        current_level.label=current_level.label+"|"+label.last_common[i]
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
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='-NONE-'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels): 
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='-NONE-'):
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
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label=='-NONE-'):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, stanzatree('-NONE-',[]))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels): 
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label=='-NONE-'):
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

ENCODINGS_MAP = {
    C_ABSOLUTE_ENCODING:{'encoder':c_absolute_encoder,'decoder':c_absolute_decoder},
    C_RELATIVE_ENCODING:{'encoder':c_relative_encoder,'decoder':c_relative_decoder},
    C_DYNAMIC_ENCODING:{'encoder':c_dynamic_encoder,'decoder':c_dynamic_decoder},
}

# given a tree encodes it and writes the label to a file
def encode_single(tree, e):
    labels, pos_tags, words = e.encode(tree)

    # linearized tree will be shaped like
    # (WORD  POSTAG  LABEL)
    lt=[]
    lt.append(u" ".join(('-BOS-','-BOS-','-BOS-')))
    for l, p, w in zip(labels, pos_tags, words):
        lt.append(u" ".join((w, p, str(l))))
    lt.append(u" ".join(('-EOS-','-EOS-','-EOS-')))
    return lt
def encode_constituent(in_path, out_path, encoding_type,collapse_unary=False):
    trees=read_tree_file(in_path)
    f_out=open(out_path,"w+")

    e=constituent_encoder(encoding_type, collapse_unary)
    tree_counter=0
    for tree in trees:
        linearized_tree = encode_single(tree, e)
        for s in linearized_tree:
            f_out.write(s+'\n')
        f_out.write("\n")
        tree_counter+=1
    return tree_counter

# given a label file decodes it and writes the decoded to a file
def decode_single(lbls, d, nlp):
    labels = []
    words = []
    postags = []
    sentence = ""

    for lbl in lbls:
        
        split_lbl = lbl.split(" ")
        
        if len(split_lbl)==2:
            # no postags in label, use prediction
            word, label = split_lbl
        
        elif len(split_lbl)==3:
            # use golden postags
            word, postag, label = split_lbl
            postags.append(postag)
        
        sentence+=" "+word
        words.append(word)
        nc, lc, uc, et = label.split("_")
        labels.append(encoded_constituent_label(et, nc, lc, uc))

    # postag prediction with this has the problem that we encoded the unary chain
    # in the postags    
    if postags==[]:
        if nlp:
            doc = nlp(sentence)
            for element in doc.sentences:
                for word in element.words:
                    postags.append(word.upos)
        else:
            for word in words:
                postags.append("")
    
    #print(sentence)
    return d.decode(labels,zip(words, postags))
def decode_constituent(in_path, out_path, encoding_type, remove_nulls=False, predict_postags=False):
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    d=constituent_decoder(encoding_type,remove_nulls)
    nlp=None
    predict_postags=True
    if predict_postags:
        nlp = stanza.Pipeline(lang='en', processors='tokenize,pos', model_dir="./stanza_resources")

    tree_counter=0
    decoded_trees = []

    current_tree = []
    is_appending = False
    for line in f_in:
        if "-EOS-" in line:
            decoded_tree=decode_single(current_tree,d,nlp)
            f_out.write(str(decoded_tree))
            f_out.write("\n")
            tree_counter+=1
            is_appending=False
        
        if is_appending:
            current_tree.append(line.replace('\n',''))

        if "-BOS-" in line:
            current_tree=[]
            is_appending=True


    return tree_counter