from abc import ABC, abstractmethod
import re

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
        node = re.sub(r'[0-9]+', '', node)
        last_common = node.split(feature_marker)[0]
        return last_common
    
    def get_features(self, node, feature_marker="##", feature_splitter="|"):
        postag_split = node.split(feature_marker)
        feats = None

        if len(postag_split) > 1:
            postag = re.sub(r'[0-9]+', '', postag_split[0])
            feats = postag_split[1].split(feature_splitter)
        else:
            postag = re.sub(r'[0-9]+', '', node)
        return postag, feats
    
    def encode(self, constituent_tree):
        pass
    def decode(self, linearized_tree):
        pass

