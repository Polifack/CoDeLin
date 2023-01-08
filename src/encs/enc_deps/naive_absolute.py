from src.encs.abstract_encoding import ADEncoding
from src.models.deps_label import DependencyLabel
from src.models.conll_node import ConllNode

class D_NaiveAbsoluteEncoding(ADEncoding):
    def __init__(self, separator):
        super().__init__(separator)

    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            # skip dummy root
            if node.id == 0:
                continue

            li = node.relation

            # xi computation
            xi = node.head
            
            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels
    
    def decode(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]

        i = 1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)
            
            if label.xi == "-NONE-":
                label.xi = 0
            
            node.relation = label.li
            node.head = int(label.xi)

            decoded_nodes.append(node)
            i+=1
        return decoded_nodes[1:]