from src.constituent.constituent import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy

if __name__=="__main__":
    print("Start!")
    ns="(S (NULL (NP (NULL (DT This)) (NULL (NN time)))) (NULL (NULL (, ,))) (NP (DT the) (NNS firms)) (VP (NULL (VBD were)) (ADJP (JJ ready))) (. .))"
    cs="(S (NP|VP (DT This) (NN time)) (, ,) (NP (DT the) (NNS firms)) (VP (VBD were) (ADJP|ASDF|ASDF (JJ ready))) (. .))"
    s="(S (NP (DT This) (NN time)) (, ,) (NP (DT the) (ADJ old) (NNS firms)) (VP (VBD were) (ADJP (JJ ready))) (. .))"

    t = Tree.fromstring(s)
    t.pretty_print()

    e = constituent_encoder(constituent_absolute_encoder())
    e.preprocess_tree(t)
    lbl=e.encode(t)
    pt = e.get_pos_tags(t)
    
    i=0
    for label in lbl:
        print(label.last_common)
        i+=1
        if i==4:
            label.last_common="AVP"

    d = constituent_decoder(constituent_absolute_decoder())
    dt = d.decode(lbl, pt)
    
    dt.pretty_print()
    fix_conflict_nodes(dt, STRAT_MAX)
    dt.pretty_print()
