from src.constituent.constituent_stanza import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy
import time

def check_with_time():
    start_time=time.time()
    e = constituent_encoder(c_dynamic_encoder())
    d = constituent_decoder(c_dynamic_decoder())
    test_file("./test/constituency/dev.trees",e,d)
    print("[*] decoding and encoding dev.trees dyn encoding:",(time.time()-start_time))
    

if __name__=="__main__":
    check_with_time()
