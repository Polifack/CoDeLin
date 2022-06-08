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

C_NONE_LABEL = "-NONE-"
C_ROOT_LABEL = "-ROOT-"
C_END_LABEL = "-END-"

C_BOS = u" ".join(('-BOS-','-BOS-','-BOS-'))
C_EOS = u" ".join(('-EOS-','-EOS-','-EOS-'))

class encoded_constituent_label:
    def __init__(self, et, nc, lc, uc):
        self.encoding_type=et
        self.n_commons=int(nc)
        self.last_common=lc
        self.unary_chain=uc if uc!=C_NONE_LABEL else None
    
    def __repr__(self):
        uchain = ""
        if self.unary_chain:
            for element in self.unary_chain:
                uchain+="+"+element
            uchain=uchain[1:]
        else:
            uchain = C_NONE_LABEL
            
        return f'{self.n_commons}_{self.last_common}_{uchain}_{self.encoding_type}'
    
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
        tree.children=(*tree.children,Tree(C_END_LABEL,[Tree(C_END_LABEL)]))

        # collapse unary 
        if self.do_collapse:
            self.collapse_unary(tree)

        # get path_to_leaves
        path_to_leaves = self.path_to_leaves(tree)

        return self.encoder.encode(tree, path_to_leaves)
   
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

class c_relative_encoder:
    def encode(self, tree, ptl):

        labels=[]
        words=[]
        postags=[]

        last_n_common=0
        for i in range(0, len(ptl)-1):
            path_a=ptl[i]
            path_b=ptl[i+1]
            
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

                    lbl=encoded_constituent_label(C_RELATIVE_ENCODING,n_commons-last_n_common,last_common, unary_chain)
                    
                    labels.append(lbl)
                    words.append(word)
                    postags.append(postag)

                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=len(a.split("+"))
                last_common = a
        return labels, postags, words
class c_absolute_encoder:
    def encode(self, tree, ptl):

        labels=[]
        words=[]
        postags=[]

        for i in range(0, len(ptl)-1):
            path_a=ptl[i]       # path to leaves for the w
            path_b=ptl[i+1]     # path to leaves for the word w+1
            
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

                    lbl=encoded_constituent_label(C_ABSOLUTE_ENCODING, n_commons, last_common, unary_chain)
                    labels.append(lbl)
                    words.append(word)
                    postags.append(postag)
                    break
                
                # increase
                n_commons+=len(a.split("+"))
                last_common = a
        return labels, postags, words
class c_dynamic_encoder:
    def encode(self, tree, path_to_leaves):

        labels=[]
        words=[]
        postags=[]

        last_n_common=0
        
        # encoding as labels (most_deep_common_ancestor, n_common_ancestors)
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
                    
                    # abs_val <= 3 : the node n-1 and n share at most 3 levels
                    # rel_val <=-2 : the node n-1 is at least 2 levels deeper than node n
                    abs_val=n_commons
                    rel_val=(n_commons-last_n_common)
                    if (abs_val<=3 and rel_val<=-2):
                        lbl = encoded_constituent_label(C_ABSOLUTE_ENCODING, abs_val, last_common, unary_chain)
                    else:
                        lbl=encoded_constituent_label(C_RELATIVE_ENCODING,rel_val,last_common, unary_chain)

                    labels.append(lbl)
                    words.append(word)
                    postags.append(postag)

                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=len(a.split("+"))
                
                last_common = a
        
        return labels, postags, words

##############################

class constituent_decoder:
    def __init__(self, encoding, do_clean_nulls, conflict_strat=C_STRAT_MAX):
        self.decoder = ENCODINGS_MAP[encoding]['decoder']()
        self.conflict_strat=conflict_strat
        self.do_clean_nulls = do_clean_nulls

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
            
            if self.do_clean_nulls and c.label == C_NONE_LABEL:
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
                for i in range(none_child_idx, len(tree_children)-1):
                    new_children.append(tree_children[i])

                tree.children=tuple(new_children)

            if type(c) is Tree:
                self.postprocess_tree(c, c.children)

    def decode(self, labels, words, pos_tags):
        # check first label not below 0
        if labels[0].n_commons<0:
            labels[0].n_commons = 0

        decoded_tree = self.decoder.decode(labels, words, pos_tags, self.preprocess_label, self.fill_pos_nodes)
        self.postprocess_tree(decoded_tree,decoded_tree.children)
        
        return decoded_tree

class c_absolute_decoder:
    def decode(self, labels, words, postags, preprocess_label, fill_pos_nodes):
        tree = Tree(C_ROOT_LABEL,[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label, word, postag in zip(labels,words, postags):
            # preprocess the label
            preprocess_label(label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label==C_NONE_LABEL):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))  
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
                fill_pos_nodes(current_level, postag, word, label.unary_chain)
            else:
                fill_pos_nodes(old_level ,postag, word, label.unary_chain)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
        
        # remove dummy root node
        tree=tree.children[0]
        return tree
class c_relative_decoder:
    def decode(self, labels, words, pos_tags, preprocess_label, fill_pos_nodes):
        tree = Tree(C_ROOT_LABEL,[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label, word, pos_tag in zip(labels, words, pos_tags):
            # preprocess the label
            preprocess_label(label)
            if last_label!=None:
                label.to_absolute(last_label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label==C_NONE_LABEL):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))  
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
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                fill_pos_nodes(current_level, pos_tag, word, label.unary_chain)
            else:
                fill_pos_nodes(old_level, pos_tag, word, label.unary_chain)

            old_n_commons=label.n_commons
            old_last_common=label.last_common
            old_level=current_level
            last_label=label
        
        # remove dummy root node
        tree=tree.children[0]
        return tree
class c_dynamic_decoder:
    def decode(self, labels, words, pos_tags, preprocess_label, fill_pos_nodes):
        tree = Tree('ROOT',[])
        current_level = tree

        old_n_commons=0
        old_last_common=''
        old_level=None
        is_first = True
        last_label = None
        for label, word, pos_tag in zip(labels,words, pos_tags):
            # preprocess the label
            preprocess_label(label)
            if last_label!=None and label.encoding_type==C_RELATIVE_ENCODING:
                label.to_absolute(last_label)
            current_level = tree

            if len(label.last_common)==1:
                # descend and create
                for level_index in range(label.n_commons):
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))
                    current_level = current_level.children[len(current_level.children)-1]
                
                # fill intermediate nodes
                if (current_level.label==C_NONE_LABEL):
                    current_level.label=label.last_common[0]
            
            else:
                # descend and create
                for level_index in range(label.n_commons): 
                    if (len(current_level.children)==0) or (level_index >= old_n_commons):
                        current_level.children = (*current_level.children, Tree(C_NONE_LABEL,[]))  
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
                    current_level=current_level.children[len(current_level.children)-1]

                # set last label
                current_level.label=label.last_common[i+1]
            
            # dealing with PoS
            if (label.n_commons >= old_n_commons):
                fill_pos_nodes(current_level, pos_tag, word, label.unary_chain)
            else:
                fill_pos_nodes(old_level, pos_tag, word, label.unary_chain)

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
    lt.append(C_BOS)
    for l, p, w in zip(labels, pos_tags, words):
        lt.append(u" ".join((w, p, str(l))))
    lt.append(C_EOS)
    
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
    return d.decode(labels, words, postags)
def decode_constituent(in_path, out_path, encoding_type, remove_nulls=False, predict_postags=False):
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    d=constituent_decoder(encoding_type,remove_nulls)
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