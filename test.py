from stanza.models.constituency.parse_tree import Tree as stanzatree
from stanza.models.constituency.tree_reader import *
from src.constituent.constituent import *

import copy
import time
import nltk

def preprocess_tree(tree):
    tree.children=(*tree.children,stanzatree("FINISH",[]))
def collapse_unary(tree):
    for child in tree.children:
        collapse_unary(child)
    if len(tree.children)==1 and not tree.is_preterminal():
            tree.label+="+"+tree.children[0].label
            tree.children=tree.children[0].children
def get_pos_tags(tree):
    return get_pos_tags_rec(tree, [])
def get_pos_tags_rec(tree,accum):
    for child in tree.children:
        get_pos_tags_rec(child,accum)
    if len(tree.children)==1 and tree.is_preterminal():
        accum.append((tree.children[0].label,tree.label))
    return accum
def path_to_leaves(tree):
    return path_to_leaves_rec(tree,[],[],0)
def path_to_leaves_rec(tree, current_path, paths, idx):
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
            path_to_leaves_rec(child, common_path, paths,idx)
            idx+=1
    return paths
def encode(tree):
    ptl = path_to_leaves(tree)
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
    print(labels)
    return labels


def preprocess_label(label):
    #  split the unary chains
    label.last_common=label.last_common.split("+")
def fill_pos_nodes(current_level, pos_tags):
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
def decode(labels, pos_tags):
    tree = stanzatree('ROOT',[])
    current_level = tree

    old_n_commons=0
    old_last_common=''
    old_level=None
    is_first = True

    for label,pos_tag in zip(labels,pos_tags):
        # preprocess the label
        preprocess_label(label)
        #print(pos_tag, label.n_commons, label.last_common)
        # reset current_level to the head of the tree
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

        #Tree.fromstring(str(tree)).pretty_print()
        old_n_commons=label.n_commons
        old_last_common=label.last_common
        old_level=current_level
    
    # remove dummy root node
    #tree=tree.children[0]

    return tree

def test_single(txt):        
    st=read_trees(txt)[0]
    nt=Tree.fromstring(txt)
    
    # stanza
    #nt.pretty_print()
    
    collapse_unary(st)
    preprocess_tree(st)
    s_postags = get_pos_tags(st)
    s_labels = encode(st)
    s_dt=decode(s_labels,s_postags)
    
    #Tree.fromstring(str(s_dt)).pretty_print()
    return (read_trees(txt)[0]==s_dt)

    # nltk
    '''
    e = constituent_encoder(constituent_absolute_encoder())
    e.preprocess_tree(nt)
    nt.pretty_print()
    n_postags=e.get_pos_tags(nt)
    n_labels = e.encode(nt)
    
    
    eq=True
    for ls,ln,npt,spt in zip(s_labels,n_labels,n_postags,s_postags):
        eq=eq and (npt==spt and ls.n_commons==ln.n_commons and ls.last_common==ln.last_common)
        print(npt,spt,"|",ln.n_commons,ls.n_commons,"|",ln.last_common,ls.last_common)
    return eq
    '''

def test_file(filepath):
    f=open(filepath)
    i=1
    for line in f:
        r=test_single(line)
        if not (r):
            print("err at",i)
        i+=1


if __name__=="__main__":
    #start_time=time.time()
    #test_file("./test/constituency/dev.trees")
    #print("[*] decoding and encoding dev.trees absolute encoding:",(time.time()-start_time))
    #start_time=time.time()
    #test_file("./test/constituency/test.trees")
    #print("[*] decoding and encoding dev.trees absolute encoding:",(time.time()-start_time))
    #start_time=time.time()
    test_file("./test/constituency/train.trees")
    #print("[*] decoding and encoding train.trees absolute encoding:",(time.time()-start_time))
    