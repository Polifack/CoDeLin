from encs.abstract_encoding import ADEncoding

from models.dependency_label import DependencyLabel
from models.conll_node import ConllNode

class D_BrkBasedEncoding(ADEncoding):
    
    def __init__(self, separator, displacement):
        super().__init__(separator)
        self.displacement = displacement

    def encode(self, nodes):
        labels_brk=["" for e in nodes]
        encoded_labels=[]
        
        # compute brackets array
        for node in nodes:
            if int(node.id)==0 or int(node.head)==0:
                continue

            if int(node.id) < int(node.head):
                labels_brk[int(node.id) + (1 if self.displacement else 0)]+='<'
                labels_brk[int(node.head)]+='\\'
            
            else:
                labels_brk[int(node.head) + (1 if self.displacement else 0)]+='/'
                labels_brk[int(node.id)]+='>'
        

        for node in nodes:
            # skip dummy root
            if node.id == 0:
                continue
            
            li = node.relation

            # xi computation
            xi = labels_brk[int(node.id)]

            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels

    def decode(self, labels, postags, words):
        decoded_nodes=[ConllNode.dummy_root()]
        for l in labels:
            decoded_nodes.append(ConllNode.empty_node())

        l_stack = []
        r_stack = []
        
        current_node = 1
        for label, postag, word in zip(labels, postags, words):
            brks=list(label.xi)
                        
            # set parameters to the node
            decoded_nodes[current_node].id = current_node
            decoded_nodes[current_node].form = word
            decoded_nodes[current_node].upos = postag
            decoded_nodes[current_node].relation = label.li

            # fill the relation using brks
            for char in brks:
                if char == "<":
                    node_id = current_node + (-1 if self.displacement else 0)
                    r_stack.append(node_id)

                if char == "\\":
                    head_id = r_stack.pop() if len(r_stack) > 0 else 0
                    decoded_nodes[head_id].head=current_node
                
                if char =="/":
                    node_id = current_node + (-1 if self.displacement else 0)
                    l_stack.append(node_id)

                if char == ">":
                    head_id = l_stack.pop() if len(l_stack) > 0 else 0
                    decoded_nodes[current_node].head=head_id
            
            current_node+=1

        return decoded_nodes[1:]