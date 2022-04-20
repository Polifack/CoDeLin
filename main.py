from src.constituent.constituent import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy

if __name__=="__main__":
    print("Start!")
    s="(SINV (`` ``) (S (NP (PRP It)) (VP (VBZ 's) (NP (NP (DT a) (NN problem)) (SBAR (WHNP (WDT that)) (S (ADVP (RB clearly)) (VP (VBZ has) (S (VP (TO to) (VP (VB be) (VP (VBN resolved))))))))))) (, ,) ('' '') (VP (VBD said)) (NP (NP (NNP David) (NNP Cooke)) (, ,) (NP (NP (JJ executive) (NN director)) (PP (IN of) (NP (DT the) (NNP RTC))))) (. .))"
    #test_file("./test/constituency/dev.trees")
    test_single(s,None)