from src.constituent.constituent_stanza import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy
import time

def check_c_with_time():
    start_time=time.time()
    e = constituent_encoder(c_dynamic_encoder())
    linearize_constituent("./test/constituency/dev.trees","./test/constituency/dev.labels",e)
    print("[*] cosntituyent encoding time:",(time.time()-start_time))

def check_d_with_time():
    start_time=time.time()
    displacement=True
    e=d_brk_2p_encoder(D_2P_PROP, displacement)
    linearize_dependencies("./test/dependencies/UD_Spanish-GSD/es_gsd-ud-dev.conllu", "./test/dependencies/UD_Spanish-GSD/es_gsd-ud-dev.labels", e)
    print("[*] dependencies encoding time:",(time.time()-start_time))

if __name__=="__main__":
    check_d_with_time()
