from codelin.encs.abstract_encoding import ADEncoding
from codelin.models.deps_label import D_Label
from codelin.models.deps_tree import D_Tree
from codelin.utils.constants import D_NONE_LABEL
from codelin.models.linearized_tree import LinearizedTree

class D_Brk4BitsEncoding(ADEncoding):
    
    def __init__(self, separator:str = "_"):
        super().__init__(separator)

    def __str__(self):
        return "Dependency Bracketing 4-Bits Encoding"


    def encode(self, dep_tree):
        n_nodes = len(dep_tree)
        labels_brk     = [""] * (n_nodes + 1)
        encoded_labels = []

        # build brackets array
        for node in dep_tree:
            if node.id == 0:
                continue
            
            if node.is_left_arc():
                labels_brk[node.id] += '<'    
                if dep_tree.is_leftmost(node):
                    labels_brk[node.id] += '*'
                
                labels_brk[node.head] += '\\' if "\\" not in labels_brk[node.head] else ""
            
            else:
                labels_brk[node.id] += '>'
                if dep_tree.is_rightmost(node):
                    labels_brk[node.id] += '*'
                
                labels_brk[node.head] += '/' if "/" not in labels_brk[node.head] else ""
        
        # generate labels
        for node in dep_tree:
            li = node.relation
            xi = labels_brk[node.id]

            current = D_Label(xi, li, self.separator)
            encoded_labels.append(current)

        return LinearizedTree(dep_tree.get_words(), dep_tree.get_postags(), dep_tree.get_feats(), encoded_labels, len(encoded_labels))

    def decode(self, lin_tree):
        # Create an empty tree with n labels
        decoded_tree = D_Tree.empty_tree(len(lin_tree))
        
        stack = []
        current_node = 0
        for word, postag, features, label in lin_tree.iterrows(dir='l2r'):
            brks = list(label.xi) if label.xi != D_NONE_LABEL else []
            for i in range(len(brks)):
                if brks[i] == "*":
                    brks[i-1] = brks[i-1] + "*"
                    brks[i] = ""
            brks = [brk for brk in brks if brk != ""]
                       
            # set parameters to the node
            decoded_tree.update_word(current_node, word)
            decoded_tree.update_upos(current_node, postag)
            decoded_tree.update_relation(current_node, label.li)

            # fill the relation using brks
            for char in brks:                
                if "/" in char:
                    stack.append(current_node)
                if ">" in char:
                    head_id = stack[-1] if len(stack) > 0 else 0
                    decoded_tree.update_head(current_node, head_id)
                    if "*" in char:
                        stack.pop()
            
            current_node+=1

        stack = []
        current_node = len(lin_tree)-1
        for word, postag, features, label in lin_tree.iterrows(dir='r2l'):
            # get the brackets
            brks = list(label.xi) if label.xi != D_NONE_LABEL else []
            # merge * with the brackets
            for i in range(len(brks)):
                if brks[i] == "*":
                    brks[i-1] = brks[i-1] + "*"
                    brks[i] = ""
            brks = [brk for brk in brks if brk != ""]
            
            # sort brackets with < first and \ last
            brks.sort(key = lambda x: (x == "\\", x))
            
            # set parameters to the node
            decoded_tree.update_word(current_node, word)
            decoded_tree.update_upos(current_node, postag)
            decoded_tree.update_relation(current_node, label.li)
            # fill the relation using brks
            for char in brks:
                if "\\" in char:
                    stack.append(current_node)  
                if "<" in char:
                    head_id = stack[-1] if len(stack) > 0 else 0
                    decoded_tree.update_head(current_node, head_id)
                    if "*" in char:
                        stack.pop()

            current_node -= 1

        decoded_tree.remove_dummy()
        return decoded_tree