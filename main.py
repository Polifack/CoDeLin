from src.constituent.constituent import * 
from src.dependency.dependency import *
from nltk.tree import Tree, ParentedTree
import copy

if __name__=="__main__":

    #test_file("./test/constituency/dev.trees",C_ABSOLUTE_ENCODING)
    
    #test_file("./test/constituency/test.trees",C_ABSOLUTE_ENCODING)
    
    #test_file("./test/constituency/train.trees",C_ABSOLUTE_ENCODING)

    #test_file("./test/constituency/dev.trees",C_RELATIVE_ENCODING)
    
    #test_file("./test/constituency/test.trees",C_RELATIVE_ENCODING)
    
    #test_file("./test/constituency/train.trees",C_RELATIVE_ENCODING)

    test_file("./test/constituency/dev.trees",C_DYNAMIC_ENCODING)
    
    test_file("./test/constituency/test.trees",C_DYNAMIC_ENCODING)
    
    test_file("./test/constituency/train.trees",C_DYNAMIC_ENCODING)