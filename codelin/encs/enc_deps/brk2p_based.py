from codelin.encs.abstract_encoding import ADEncoding
from codelin.utils.constants import D_2P_GREED, D_2P_PROP, D_NONE_LABEL
from codelin.models.deps_label import D_Label
from codelin.models.deps_tree import D_Tree
from codelin.models.linearized_tree import LinearizedTree


class D_Brk2PBasedEncoding(ADEncoding):
    def __init__(self, separator:str = "_", displacement:bool = False, planar_alg:str = D_2P_GREED):
        if planar_alg and planar_alg not in [D_2P_GREED, D_2P_PROP]:
            print("[*] Error: Unknown planar separation algorithm")
            exit(1)
        super().__init__(separator)
        self.displacement = displacement
        self.planar_alg = planar_alg

    def __str__(self):
        return "Dependency 2-Planar Bracketing Based Encoding"

    def encode(self, dep_tree):
        def encoding_step(disp, plane, lbl_brk, brk_chars):
            for node in plane:
                # skip root relations (optional?)
                if node.head == 0:
                    continue
                
                if node.id < node.head:
                    if disp:
                        lbl_brk[node.id+1]+=brk_chars[3]
                    else:
                        lbl_brk[node.id]+=brk_chars[3]

                    lbl_brk[node.head]+=brk_chars[2]
                
                else:
                    if disp:
                        lbl_brk[node.head+1]+=brk_chars[1]
                    else:
                        lbl_brk[node.head]+=brk_chars[1]

                    lbl_brk[node.id]+=brk_chars[0]
            
            return lbl_brk

        # create brackets array
        n_nodes = len(dep_tree)
        labels_brk = [""] * (n_nodes + 1)

        # separate the planes
        if self.planar_alg == D_2P_GREED:
            p1_nodes, p2_nodes = D_Tree.two_planar_greedy(dep_tree)
        elif self.planar_alg == D_2P_PROP:
            p1_nodes, p2_nodes = D_Tree.two_planar_propagate(dep_tree)

        # get brackets separatelly
        labels_brk = encoding_step(self.displacement, p1_nodes, labels_brk, ['>','/','\\','<'])
        labels_brk = encoding_step(self.displacement, p2_nodes, labels_brk, ['>*','/*','\\*','<*'])
        
        # merge and obtain labels
        lbls=[]
        dep_tree.remove_dummy()
        for node in dep_tree:
            xi = labels_brk[node.id]
            li = node.relation
            if xi=="":
                xi=D_NONE_LABEL

            current = D_Label(xi, li, self.separator)
            lbls.append(current)
        
        return LinearizedTree(dep_tree.get_words(), dep_tree.get_postags(), dep_tree.get_feats(), lbls, len(lbls))

    def decode(self, lin_tree):
        decoded_tree = D_Tree.empty_tree(len(lin_tree)+1)
        
        # create plane stacks
        l_stack_p1=[]
        l_stack_p2=[]
        r_stack_p1=[]
        r_stack_p2=[]
        
        current_node=1

        for word, postag, features, label in lin_tree.iterrows():
            brks = list(label.xi) if label.xi != D_NONE_LABEL else []
            temp_brks=[]
            
            for i in range(0, len(brks)):
                current_char=brks[i]
                if brks[i]=="*":
                    current_char=temp_brks.pop()+brks[i]
                temp_brks.append(current_char)
                    
            brks=temp_brks
            
            # set parameters to the node
            decoded_tree.update_word(current_node, word)
            decoded_tree.update_upos(current_node, postag)
            decoded_tree.update_relation(current_node, label.li)
            
            # fill the relation using brks
            for char in brks:
                if char == "<":
                    node_id=current_node + (-1 if self.displacement else 0)
                    r_stack_p1.append((node_id,char))
                
                if char == "\\":
                    head_id = r_stack_p1.pop()[0] if len(r_stack_p1)>0 else 0
                    decoded_tree.update_head(head_id, current_node)
                
                if char =="/":
                    node_id=current_node + (-1 if self.displacement else 0)
                    l_stack_p1.append((node_id,char))

                if char == ">":
                    head_id = l_stack_p1.pop()[0] if len(l_stack_p1)>0 else 0
                    decoded_tree.update_head(current_node, head_id)

                if char == "<*":
                    node_id=current_node + (-1 if self.displacement else 0)
                    r_stack_p2.append((node_id,char))
                
                if char == "\\*":
                    head_id = r_stack_p2.pop()[0] if len(r_stack_p2)>0 else 0
                    decoded_tree.update_head(head_id, current_node)
                
                if char =="/*":
                    node_id=current_node + (-1 if self.displacement else 0)
                    l_stack_p2.append((node_id,char))

                if char == ">*":
                    head_id = l_stack_p2.pop()[0] if len(l_stack_p2)>0 else 0
                    decoded_tree.update_head(current_node, head_id)
            
            current_node+=1

        decoded_tree.remove_dummy()
        return decoded_tree   
