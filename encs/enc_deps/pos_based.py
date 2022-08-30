from encs.abstract_encoding import ADEncoding

from models.dependency_label import DependencyLabel
from models.conll_node import ConllNode

from utils.constants import D_POSROOT

class D_PosBasedEncoding(ADEncoding):
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
            node_head = int(node.head)
            node_id = int(node.id)
            
            pi = nodes[node_head].upos
            oi = 0

            # if not root, compute the oi value
            if node_head != 0:
                step = 1 if node_id < node_head else -1

                for i in range(node_id, node_head+step, step):
                    if pi == nodes[i].upos:
                        oi += step

            xi = str(oi)+"--"+pi

            current=DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels

    def decode(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]
        
        i = 1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)

            node.relation = label.li
            
            if label.xi == "-NONE-":
                label.xi = "0--ROOT"

            oi, pi = label.xi.split('--')            

            oi = int(oi)

            # ROOT is a special case
            if (pi==D_POSROOT or oi==0):
                node.head = 0
                decoded_nodes.append(node)
                
                i+=1
                continue

            # store the value of pi (number of oi found) to substract it
            target_oi = oi

            # create the step and the stop point 
            step = 1 if oi > 0 else -1
            stop_point = (len(postags)+1) if oi > 0 else 0

            for j in range (node.id, stop_point, step):                  
                if (pi == postags[j-1]):
                    target_oi -= step
                
                if (target_oi==0):
                    break       
            
            node.head = j
            
            decoded_nodes.append(node)
            i+=1
        
        return decoded_nodes[1:]