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
C_STRAT_NONE="strat_none"

C_NONE_LABEL = "-NONE-"
C_ROOT_LABEL = "-ROOT-"
C_END_LABEL = "-END-"
C_CONFLICT_SEPARATOR = "-||-"

C_BOS = '-BOS-'
C_EOS = '-EOS-'

class encoded_constituent_label:
    def __init__(self, nc, lc, uc, et, sp, uj):
        self.encoding_type = et
        self.n_commons=int(nc)
        self.last_common=lc
        self.unary_chain=uc if uc!=C_NONE_LABEL else None
        self.separator=sp
        self.unary_joiner=uj
    
    def __repr__(self):
        # build the unary_string
        unary_str = self.unary_joiner.join([self.unary_chain]) if self.unary_chain else ""

        return (str(self.n_commons) + ("*" if self.encoding_type==C_RELATIVE_ENCODING else "")
        + self.separator + self.last_common + (self.separator + unary_str if self.unary_chain else ""))
    
    def to_absolute(self, last_label):
        self.n_commons+=last_label.n_commons
        # if the n_commons after getting absolutized is negative
        # it was a bad prediction, hang it from the root
        if self.n_commons<=0:
            self.n_commons = 1
        
        self.encoding_type=C_ABSOLUTE_ENCODING

##############################

class constituent_encoder:
    def __init__(self, encoding, separator, unary_joiner):
        self.encoding = encoding
        self.separator = separator
        self.unary_joiner = unary_joiner

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
        additional_feats=[]

        last_n_common=0
        for i in range(0, len(path_to_leaves)-1):
            path_a=path_to_leaves[i]
            path_b=path_to_leaves[i+1]
            
            last_common=""
            n_commons=0
            for a,b in zip(path_a, path_b):
                # if we have an ancestor that is not common break
                if (a!=b):
                    # remove the digits (only in the postag part, ignore the ## part)
                    last_common=re.sub(r'[0-9]+', '', last_common)

                    word = path_a[-1]
                    postag = path_a[-2]
                    
                    unary_chain = None 

                    postag_list=postag.split(self.unary_joiner)
                    if len(postag.split(self.unary_joiner))>1:
                        unary_chain=self.unary_joiner.join(postag_list[:-1])
                        postag=postag_list[-1]
                    
                    # clean postag and get additional feats if exitt
                    postag, c_additional_feats, _ = postag.split("##") if len(postag.split("##"))>1 else (re.sub(r'[0-9]+', '', postag), None, None)
                    
                    # get values for absolute encoding/relative encoding
                    abs_val=n_commons
                    rel_val=(n_commons-last_n_common)

                    # create labels according the encoder selected
                    if self.encoding == C_ABSOLUTE_ENCODING:
                        lbl=encoded_constituent_label(n_commons, last_common, unary_chain, C_ABSOLUTE_ENCODING, self.separator, self.unary_joiner)
                    elif self.encoding == C_RELATIVE_ENCODING:
                        lbl=encoded_constituent_label(rel_val, last_common, unary_chain, C_RELATIVE_ENCODING, self.separator, self.unary_joiner)
                    else:
                        if (abs_val<=3 and rel_val<=-2):
                            lbl = encoded_constituent_label(abs_val, last_common, unary_chain, C_ABSOLUTE_ENCODING, self.separator, self.unary_joiner)
                        else:
                            lbl=encoded_constituent_label(rel_val,last_common, unary_chain, C_RELATIVE_ENCODING, self.separator, self.unary_joiner)
                    
                    # append the labels, words postags and feats if we need them
                    labels.append(lbl)
                    words.append(word)
                    postags.append(postag)
                    
                    if c_additional_feats:
                        additional_feats.append(c_additional_feats.split("|"))

                    last_n_common=n_commons
                    break
                
                # increase
                n_commons+=len(a.split(self.unary_joiner))
                last_common = a
        return words, postags, labels, additional_feats

    def collapse_unary(self, tree):
        for child in tree.children:
            self.collapse_unary(child)
        if len(tree.children)==1 and not tree.is_preterminal():
                tree.label+=self.unary_joiner+tree.children[0].label
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
    def __init__(self, encoding, conflict_strat, unary_joiner):
        self.encoding = encoding
        self.conflict_strat=conflict_strat
        self.unary_joiner=unary_joiner

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
                
                # if the current level is NULL, set it to label
                if (current_level.label==C_NONE_LABEL):
                    current_level.label=label.last_common[0]
                
                # if the current level has a label different for the current one, append it
                elif current_level.label != label.last_common[0]:
                    current_level.label=current_level.label+C_CONFLICT_SEPARATOR+label.last_common[0]
            
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
                
                for i in range(len(label.last_common)-1):
                    if (current_level.label==C_NONE_LABEL):
                        current_level.label=label.last_common[i]
                    
                    elif current_level.label != label.last_common[1]:
                        current_level.label=current_level.label+C_CONFLICT_SEPARATOR+label.last_common[i]
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
        self.postprocess_tree(tree)
        return tree

    def preprocess_label(self, label):
        #  split the unary chains
        label.last_common=label.last_common.split(self.unary_joiner)

    def fill_pos_nodes(self, current_level, postag, word, unary_chain):
        if unary_chain:
            unary_chain=unary_chain.split(self.unary_joiner)
            unary_chain.reverse()
            pos_tree = Tree(postag, Tree(word))
            for node in unary_chain:
                temp_tree=Tree(node, pos_tree)
                pos_tree=temp_tree

        else:
            pos_tree=Tree(postag, Tree(word))

        current_level.children=(*current_level.children,pos_tree)

    def check_conflicts(self, node):
        if C_CONFLICT_SEPARATOR in node.label:
            labels=node.label.split(C_CONFLICT_SEPARATOR)
            if self.conflict_strat == C_STRAT_MAX:
                node.label=max(set(labels), key=labels.count)
            if self.conflict_strat == C_STRAT_FIRST:
                node.label=labels[0]
            if self.conflict_strat == C_STRAT_LAST:
                node.label=labels[len(labels)-1]
    def check_nulls_root(self, node):
        if node.label == C_NONE_LABEL:
            node.label = C_ROOT_LABEL
    def check_nulls_child(self, tree, tree_children, child):
        if child.label == C_NONE_LABEL:
            new_children = []
            none_child_idx = tree_children.index(child)
            # append children to the "left"
            for i in range(0, none_child_idx):
                new_children.append(tree_children[i])

            # foreach of the children of the node that has a null label
            # append them to the parent
            for nc in child.children:
                new_children.append(Tree(nc.label, nc.children))

            # append children to the "right"
            for j in range(none_child_idx+1, len(tree_children)):
                new_children.append(tree_children[j])

            tree.children=tuple(new_children)  
    def postprocess_tree_childs(self, tree, tree_children):
        for c in tree_children:
            self.check_conflicts(c)
            self.check_nulls_child(tree, tree_children, c)

            if type(c) is Tree:
                self.postprocess_tree_childs(c, c.children)  
    def postprocess_tree(self, tree):
        self.check_conflicts(tree)
        self.check_nulls_root(tree)

        self.postprocess_tree_childs(tree, tree.children)

def extract_features(trees):
    # parses all trees in the file and returns a list of the features
    # sorted by alphabetical order
    feats_list=set()
    for tree in trees:
        postags = tree.yield_preterminals()
        
        for postag in postags:
            feats = postag.label.split("##")[1].split("|")
            for feat in feats:
                fs = feat.split("=")
                if len(fs)>1:
                    key=fs[0]
                    feats_list.add(key)

    
    return sorted(feats_list)
                    

def encode_constituent(in_path, out_path, encoding_type, separator, unary_joiner, features):

    # test constituents with previous instead of nexts

    trees=read_tree_file(in_path)
    f_out=open(out_path,"w+")

    encoder = constituent_encoder(encoding_type, separator, unary_joiner)
    
    tree_counter=0
    labels_counter=0

    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    for tree in trees:
        words, pos_tags, labels, additional_feats = encoder.encode(tree)
        linearized_tree=[]
        linearized_tree.append(u" ".join(([C_BOS] * (3 + (len(features) if features else 0)))))
        
        for l, p, w, af in zip(labels, pos_tags, words, additional_feats):
            # create the output line of the linearized tree
            output_line = [w,p]

            # check for additional information inside the postag label
            if features:
                f_list = ["_"] * len(features)
                for element in af:
                    key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                    if key in f_idx_dict.keys():
                        f_list[f_idx_dict[key]] = value
                
                # append the additional elements or the placehodler
                for element in f_list:
                    output_line.append(element)

            # add the label
            output_line.append(str(l))
                                  
            linearized_tree.append(u" ".join(output_line))
        linearized_tree.append(u" ".join(([C_EOS] * (3 + (len(features) if features else 0)))))

        for row in linearized_tree:
            labels_counter+=1
            f_out.write(row+'\n')
        f_out.write("\n")
        tree_counter+=1
    
    return labels_counter, tree_counter

# given a label file decodes it and writes the decoded to a file
def decode_single(current_tree, d, sep, uj, nlp):
    labels = []
    words = []
    postags = []
    sentence = ""

    for line in current_tree:
        columns = line.split(" ")
        
        if len(columns)==2:
            # decoding a predicted file
            # only words and labels
            word, label = columns
        
        else:
            # decoding a gold file
            # postags and feats included
            word=columns[0]
            postag=columns[1]
            label=columns[-1]
            postags.append(postag)
        
        sentence+=" "+word
        words.append(word)
        label_components = label.split(sep)
        
        # get data from label
        if len(label_components)== 2:
            nc, lc = label_components
            uc=None
        else:
            nc, lc, uc = label_components
        
        et = C_RELATIVE_ENCODING if '*' in nc else C_ABSOLUTE_ENCODING
        nc = nc.replace("*","")
        labels.append(encoded_constituent_label(nc, lc, uc, et, sep, uj))

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
def decode_constituent(in_path, out_path, encoding_type, separator, unary_joiner, conflicts, predict_postags, language):
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    decoder = constituent_decoder(encoding_type, conflicts, unary_joiner)
    
    nlp=None
    if predict_postags:
        # stanza.download(lang=lang, model_dir="~/stanza_resources")
        nlp = stanza.Pipeline(lang=language, processors='tokenize,pos', model_dir="~/stanza_resources")

    tree_counter=0
    labels_counter=0

    decoded_trees = []

    current_tree = []
    is_appending = False
    for line in f_in:
        if C_BOS in line:
            current_tree=[]
            continue
        
        if C_EOS in line:
            decoded_tree = decode_single(current_tree, decoder, separator, unary_joiner, nlp)
            f_out.write(str(decoded_tree))
            f_out.write("\n")
            tree_counter+=1
            continue
        
        current_tree.append(line.replace('\n',''))
        labels_counter+=1



    return tree_counter,labels_counter