from stanza.models.constituency.parse_tree import Tree
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
C_CONFLICTS_NONE="strat_none"

C_NONE_LABEL = "-NONE-"
C_ROOT_LABEL = "-ROOT-"
C_END_LABEL = "-END-"

C_BOS = u" ".join(('-BOS-','-BOS-','-BOS-'))
C_EOS = u" ".join(('-EOS-','-EOS-','-EOS-'))

class encoded_constituent_label:
    def __init__(self, nc, lc, uc, et):
        self.encoding_type = et
        self.n_commons=int(nc)
        self.last_common=lc
        self.unary_chain=uc if uc!=C_NONE_LABEL else None
    
    def __repr__(self):
        if self.unary_chain:
            uchain=""
            if (len(self.unary_chain.split("+"))>1):
                for element in self.unary_chain:
                    uchain+="+"+element
                uchain=uchain[1:]
            else:
                uchain = self.unary_chain
            
        return f'{self.n_commons}{"*" if self.encoding_type==C_RELATIVE_ENCODING else ""}_{self.last_common}{"_"+uchain if self.unary_chain else ""}'
    
    def to_absolute(self, last_label):
        self.n_commons+=last_label.n_commons
        # if the n_commons after getting absolutized is negative
        # it was a bad prediction, hang it from the root
        if self.n_commons<=0:
            self.n_commons = 1
        
        self.encoding_type=C_ABSOLUTE_ENCODING

##############################

class constituent_encoder:
    def __init__(self, encoding):
        self.encoding = encoding

    def encode(self, tree):
        # add finish point to ensure all labels are encoded
        tree.children=(*tree.children,Tree(C_END_LABEL,[Tree(C_END_LABEL)]))

        # collapse unary 
        self.collapse_unary(tree)

        # get path_to_leaves
        path_to_leaves = self.path_to_leaves(tree)

        labels=[]
        words=[]
        postags=[]

        last_n_common=0
        for i in range(0, len(path_to_leaves)-1):
            path_a=path_to_leaves[i]
            path_b=path_to_leaves[i+1]
            
            last_common=""
            n_commons=0
            for a,b in zip(path_a, path_b):
                # if we have an ancestor that is not common break
                if (a!=b):
                    last_common=re.sub(r'[0-9]+', '', last_common)

                    word = path_a[-1]
                    postag = re.sub(r'[0-9]+', '',path_a[-2])
                    unary_chain = None 

                    postag_list=postag.split("+")
                    if len(postag.split("+"))>1:
                        unary_chain=postag_list[:-1]
                        postag=postag_list[-1]

                    # get values for absolute encoding/relative encoding
                    abs_val=n_commons
                    rel_val=(n_commons-last_n_common)

                    # create labels according the encoder selected
                    if self.encoding == C_ABSOLUTE_ENCODING:
                        lbl=encoded_constituent_label(n_commons, last_common, unary_chain, C_ABSOLUTE_ENCODING)
                    elif self.encoding == C_RELATIVE_ENCODING:
                        lbl=encoded_constituent_label(rel_val, last_common, unary_chain, C_RELATIVE_ENCODING)
                    else:
                        if (abs_val<=3 and rel_val<=-2):
                            lbl = encoded_constituent_label(abs_val, last_common, unary_chain, C_ABSOLUTE_ENCODING)
                        else:
                            lbl=encoded_constituent_label(rel_val,last_common, unary_chain, C_RELATIVE_ENCODING)
                    
                    labels.append(lbl)
                    words.append(word)
                    postags.append(postag)

                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=len(a.split("+"))
                last_common = a
        return labels, postags, words
   
    def collapse_unary(self, tree):
        for child in tree.children:
            self.collapse_unary(child)
        if len(tree.children)==1 and not tree.is_preterminal():
                tree.label+="+"+tree.children[0].label
                tree.children=tree.children[0].children

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

##############################

class constituent_decoder:
    def __init__(self, encoding, conflict_strat=C_STRAT_MAX):
        self.encoding = encoding
        self.conflict_strat=conflict_strat

    def decode(self, labels, words, postags):
        # check first label not below 0
        if labels[0].n_commons<0:
            labels[0].n_commons = 0
        
        # create tree
        tree = Tree(C_ROOT_LABEL)
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label, word, postag in zip(labels, words, postags):
            # preprocess the label
            self.preprocess_label(label)
            if label.encoding_type==C_RELATIVE_ENCODING and last_label!=None:
                label.to_absolute(last_label)
        
            current_level = tree
            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label==C_NONE_LABEL):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL))  
                    current_level = current_level.children[len(current_level.children)-1]
                
                # descend to the beginning of the chain
                descend_levels = label.n_commons-(len(label.last_common))+1
                current_level = tree
                for level_index in range(descend_levels):
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                for i in range(len(label.last_common)-1):
                    if (current_level.label==C_NONE_LABEL):
                        current_level.label=label.last_common[i]
                    else:
                        current_level.label=current_level.label+"|"+label.last_common[i]
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                self.fill_pos_nodes(current_level, postag, word, label.unary_chain)
            else:
                self.fill_pos_nodes(old_level ,postag, word, label.unary_chain)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
            last_label=label
        
        # remove dummy root node
        tree=tree.children[0]
        # remove nulls and conflicts
        self.postprocess_tree(tree,tree.children)
        return tree

    def preprocess_label(self, label):
        #  split the unary chains
        label.last_common=label.last_common.split("+")

    def fill_pos_nodes(self, current_level, postag, word, unary_chain):
        if unary_chain:
            unary_chain=unary_chain.split("+")
            unary_chain.reverse()
            pos_tree = Tree(postag, Tree(word))
            for node in unary_chain:
                temp_tree=Tree(node, pos_tree)
                pos_tree=temp_tree

        else:
            pos_tree=Tree(postag, Tree(word))

        current_level.children=(*current_level.children,pos_tree)

    def postprocess_tree(self, tree, tree_children):
        for c in tree_children:
            if "|" in  c.label:
                labels=c.label.split("|")
                if self.conflict_strat == C_STRAT_MAX:
                    c.label=max(set(labels), key=labels.count)
                if self.conflict_strat == C_STRAT_FIRST:
                    c.label=labels[0]
                if self.conflict_strat == C_STRAT_LAST:
                    c.label=labels[len(labels)-1]

            if c.label == C_NONE_LABEL:
                new_children = []
                none_child_idx = tree_children.index(c)
                # append children to the "left"
                for i in range(0, none_child_idx):
                    new_children.append(tree_children[i])

                # foreach of the children of the node that has a null label
                # append them to the parent
                for nc in c.children:
                    new_children.append(Tree(nc.label, nc.children))

                # append children to the "right"
                for j in range(none_child_idx+1, len(tree_children)):
                    new_children.append(tree_children[j])

                tree.children=tuple(new_children)

            if type(c) is Tree:
                self.postprocess_tree(c, c.children)

# given a tree encodes it and writes the label to a file
def encode_single(tree, e):
    labels, pos_tags, words = e.encode(tree)

    # linearized tree will be shaped like
    # (WORD  POSTAG  LABEL)
    lt=[]
    lt.append(C_BOS)
    for l, p, w in zip(labels, pos_tags, words):
        lt.append(u" ".join((w, p, str(l))))
    lt.append(C_EOS)

    return lt
def encode_constituent(in_path, out_path, encoding_type):
    trees=read_tree_file(in_path)
    f_out=open(out_path,"w+")

    e=constituent_encoder(encoding_type)
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
        label_split = label.split("_")
        
        # get data from label
        if len(label_split)== 2:
            nc, lc = label_split
            uc=None
        else:
            nc, lc, uc = label_split
        
        et = C_RELATIVE_ENCODING if '*' in nc else C_ABSOLUTE_ENCODING
        nc = nc.replace("*","")
        labels.append(encoded_constituent_label(nc, lc, uc, et))

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
    
    return d.decode(labels, words, postags)
def decode_constituent(in_path, out_path, encoding_type, conflicts, predict_postags):
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    d=constituent_decoder(encoding_type, conflicts)
    nlp=None
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