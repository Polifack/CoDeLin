from src.constituent.constituent import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy
import time

def check_with_time():
    start_time=time.time()
    test_file("./test/constituency/dev.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding dev.trees absolute encoding:",(time.time()-start_time))

    '''
    start_time=time.time()
    test_file("./test/constituency/dev.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding dev.trees relative encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/dev.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding dev.trees dynamic encoding:",(time.time()-start_time))
    '''
    start_time=time.time()
    test_file("./test/constituency/test.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding test.trees absolute encoding:",(time.time()-start_time))
    
    '''
    start_time=time.time()
    test_file("./test/constituency/test.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding test.trees relative encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/test.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding test.trees dynamic encoding:",(time.time()-start_time))
    
    start_time=time.time()
    test_file("./test/constituency/train.trees",C_ABSOLUTE_ENCODING)
    print("[*] decoding and encoding train.trees absolute encoding:",(time.time()-start_time))

    start_time=time.time()
    test_file("./test/constituency/train.trees",C_RELATIVE_ENCODING)
    print("[*] decoding and encoding train.trees relative encoding:",(time.time()-start_time))

    start_time=time.time()
    test_file("./test/constituency/train.trees",C_DYNAMIC_ENCODING)
    print("[*] decoding and encoding train.trees dynamic encoding:",(time.time()-start_time))
    '''
if __name__=="__main__":
    check_with_time()