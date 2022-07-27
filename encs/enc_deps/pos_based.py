from encs.abstract_encoding import ADEncoding

from models.dependency_label import DependencyLabel
from models.conll_node import ConllNode

class D_PosBasedEncoding(ADEncoding):
    def __init__(self, separator):
        super().__init__(separator)
        
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            if node.id == 0:
                continue

            li = node.relation
            xi = str(int(node.head)-int(node.id))
            
            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels

    def decode(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]
        
        i = 1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)

            node.relation = label.li
            node.head = int(label.xi)+node.id

            decoded_nodes.append(node)
            i+=1
        
        return decoded_nodes[1:]