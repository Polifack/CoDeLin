from abc import ABC, abstractmethod
import re
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

class ADEncoding(ABC):
    '''
    Abstract class for Dependency Encodings
    Sets the main constructor method and defines the methods
        - Encode
        - Decode
    When adding a new Dependency Encoding it must extend this class
    and implement those methods
    '''
    def __init__(self, separator):
        self.separator = separator
    
    def encode(self, constituent_tree):
        pass
    def decode(self, linearized_tree):
        pass

class ACEncoding(ABC):
    '''
    Abstract class for Constituent Encodings
    Sets the main constructor method and defines the abstract methods
        - Encode
        - Decode
    When adding a new Constituent Encoding it must extend this class
    and implement those methods
    '''
    def __init__(self, separator, ujoiner, reverse):
        self.separator = separator
        self.unary_joiner = ujoiner
        self.reverse = reverse
    
    def batch_encode(self, tree_list):
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            return list(executor.map(self.encode, tree_list))
    
    def get_unary_chain(self, postag):
        unary_chain = None
        leaf_unary_chain = postag.split(self.unary_joiner)

        if len(leaf_unary_chain)>1:
            unary_list = []
            for element in leaf_unary_chain[:-1]:
                unary_list.append(element.split("##")[0])

            unary_chain = self.unary_joiner.join(unary_list)
            postag = leaf_unary_chain[len(leaf_unary_chain)-1]
        
        return unary_chain, postag

    def clean_last_common(self, node, feature_marker="##"):
        node = re.sub(r'\[\d+\]', '', node)
        last_common = node.split(feature_marker)[0]
        return last_common
    
    def get_features(self, node, feature_marker="##", feature_splitter="|"):
        # create regex to remove characters between feature_marker
        pattern = fr"^(.*){feature_marker}(.*){feature_marker}(.*)$"
        match = re.match(pattern, node)
        if match:
            postag = match.group(1)
            feats = match.group(2).split(feature_splitter) if match.group(2) else None
        else:
            postag = re.sub(r'\[\d+\]', '', node)
            feats = None
        
        return postag, feats
    
    def encode(self, constituent_tree):
        pass
    def decode(self, linearized_tree):
        pass

