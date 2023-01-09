from src.encs.abstract_encoding import ADEncoding
from src.models.deps_label import DependencyLabel
from src.models.deps_tree import DependencyTree
from src.utils.constants import D_POSROOT, D_NONE_LABEL

POS_ROOT_LABEL = "0--ROOT"

class D_PosBasedEncoding(ADEncoding):
    def __init__(self, separator):
        super().__init__(separator)
        
    def encode(self, dep_tree):
        encoded_labels = []
        
        for node in dep_tree:
            if node.id == 0:
                # skip dummy root
                continue

            li = node.relation     
            pi = dep_tree[node.head].upos           
            oi = 0
            
            # move left or right depending if the node 
            # dependency edge is to the left or to the right

            step = 1 if node.id < node.head else -1
            for i in range(node.id + step, node.head + step, step):
                if pi == dep_tree[i].upos:
                    oi += step

            xi = str(oi)+"--"+pi

            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        dep_tree.remove_dummy()
        return encoded_labels

    def decode(self, labels, postags, words):
        dep_tree = DependencyTree.empty_tree(len(labels)+1)

        for i in range(len(labels)):
            label  = labels[i]
            postag = postags[i]
            word   = words[i]

            node_id = i+1
            if label.xi == D_NONE_LABEL:
                label.xi = POS_ROOT_LABEL
            
            dep_tree.update_word(node_id, word)
            dep_tree.update_upos(node_id, postag)
            dep_tree.update_relation(node_id, label.li)
            
            oi, pi = label.xi.split('--')
            oi = int(oi)

            # Set head for root
            if (pi==D_POSROOT or oi==0):
                dep_tree.update_head(node_id, 0)
                continue

            # Compute head position
            target_oi = oi

            step = 1 if oi > 0 else -1
            stop_point = (len(postags)+1) if oi > 0 else 0

            for j in range (node_id+step, stop_point, step):
                if (pi == postags[j-1]):
                    target_oi -= step
                
                if (target_oi==0):
                    break
            
            head_id = j
            dep_tree.update_head(node_id, head_id)

        dep_tree.remove_dummy()
        return dep_tree