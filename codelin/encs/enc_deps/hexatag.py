from codelin.encs.abstract_encoding import ADEncoding
from codelin.models.deps_label import D_Label
from codelin.models.deps_tree import D_Tree
from codelin.models.const_tree import C_Tree
from codelin.utils.constants import D_NONE_LABEL, D_2P_GREED, D_2P_PROP
from codelin.models.linearized_tree import LinearizedTree

class D_HexatagEncoding(ADEncoding):
    
    def __init__(self, separator:str = "_"):
        super().__init__(separator)

    def __str__(self):
        return "Dependency Bracketing Hexa-Tags Encoding"

    def encode(self, dep_tree):
        bht_tree = D_Tree.to_bht(dep_tree)
        inorder_traversal = []
        C_Tree.inorder(bht_tree, lambda x: inorder_traversal.append(x))

        def get_hexalabel(node):
            '''
            Returns the hexa-tag label of the node:

                'r'  =>  node is terminal and right child of its parent
                'l'  =>  node is terminal and left child of its parent
                
                'RR' =>  node is non-terminal right child and the label of its parent is 'R'
                'RL' =>  node is non-terminal right child and the label of its parent is 'L'
                
                'LR' =>  node is non-terminal left child and the label of its parent is 'R'
                'LL' =>  node is non-terminal left child and the label of its parent is 'L'
            '''

            if node.is_terminal():
                if node.is_right_child():
                    return "r"
                else:
                    return "l"
            else:
                # root node case
                if node.parent is None:
                    return "LL"

                if node.is_right_child():
                    return "R" + node.label
                else:
                    return "L" + node.label
        
        labels = {}
        current_label = ""
        
        trav_labels = [n.label for n in inorder_traversal]
        print(trav_labels)
        
        for node in inorder_traversal:
            hexalabel = get_hexalabel(node)
            current_label+=hexalabel
            if node.is_terminal():
                labels[int(node.label)]=current_label
                current_label = ""
            
        # sort
        labels = dict(sorted(labels.items(), key=lambda item: item[0]))
        # to list
        labels = list(labels.values())
        lin_tree = LinearizedTree(dep_tree.get_words(), dep_tree.get_postags(), dep_tree.get_feats(), labels, 0)
        return lin_tree
        
    def decode(self, lin_tree):
        def get_hexalabels(label):
            '''
            given a concatenation of hexa-tags, returns a list of hexa-tags
            '''
            hexalabels = []
            for i in range(0, len(label), 2):
                hexalabels.append(label[i:i+2])
            return hexalabels

        for word, postag, features, label in lin_tree.iterrows():
            print(word, postag, features, label)
            hexalabels = get_hexalabels(label)
            for hl in hexalabels:
                if hl == "r":
                    print("right child")
                elif hl == "l":
                    print("left child")
                elif hl == "RR":
                    print("non-terminal right child, parent label is R")
                elif hl == "RL":
                    print("non-terminal right child, parent label is L")
                elif hl == "LR":
                    print("non-terminal left child, parent label is R")
                elif hl == "LL":
                    print("non-terminal left child, parent label is L")
                else:
                    print("unknown hexa-tag label")