from src.constituent.constituent import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy
import time

def check_with_time():
    start_time=time.time()
    n_lines=test_file("./test/constituency/dev.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding dev.trees",(n_lines)," abs encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/dev.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding dev.trees",(n_lines)," rel encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/dev.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding dev.trees dyn encoding:",(time.time()-start_time))
    
    start_time=time.time()
    n_lines=test_file("./test/constituency/test.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding test.trees",(n_lines)," abs encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/test.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding test.trees",(n_lines)," rel encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/test.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding test.trees dyn encoding:",(time.time()-start_time))
    
    start_time=time.time()
    n_lines=test_file("./test/constituency/train.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding train.trees",(n_lines)," abs encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/train.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding train.trees",(n_lines)," rel encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/train.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding train.trees dyn encoding:",(time.time()-start_time))
    

if __name__=="__main__":
    check_with_time()
