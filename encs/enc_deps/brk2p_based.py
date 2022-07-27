from encs.abstract_encoding import ADEncoding

from utils.constants import D_2P_GREED, D_2P_PROP

from models.dependency_label import DependencyLabel
from models.conll_node import ConllNode

class D_Brk2PBasedEncoding(ADEncoding):
    def __init__(self, displacement, planar_alg):
        if planar_alg not in [D_2P_GREED, D_2P_PROP]:
            print("[*] Error: Unknown planar separation algorithm")
            exit(1)
        super().__init__(separator)
        self.displacement = displacement
        self.planar_alg = planar_alg


    def check_cross(self, next_arc, node):
        # las condiciones para que dos nodos se crucen son:
        #   id del next_arc esta entre la cabeza y el id del nodo siendo comprobado
        #   cabeza del next_arc no esta entre la cabeza y el id del nodo siendo comprobado
        # o
        #   id del next_arc no esta entre la cabeza y el id del nodo siendo comprobado
        #   cabeza del next_arc esta entre la cabeza y el id del nodo siendo comprobado
        #
        # hay que tener en cuenta que si las cabezas coinciden *no* es un cruce
        
                
        if ((next_arc.head == node.head) or (next_arc.head==node.id)):
             return False

        r_id_inside = (node.head < next_arc.id < node.id)
        l_id_inside = (node.id < next_arc.id < node.head)

        id_inside = r_id_inside or l_id_inside

        r_head_inside = (node.head < next_arc.head < node.id)
        l_head_inside = (node.id < next_arc.head < node.head)

        head_inside = r_head_inside or l_head_inside

        return head_inside^id_inside

    def get_next_edge(self, nodes, idx_l, idx_r):
        next_arc=None

        if nodes[idx_l].head==idx_r:
            next_arc = nodes[idx_l]
        
        elif nodes[idx_r].head==idx_l:
            next_arc = nodes[idx_r]
        
        return next_arc

    def two_planar_propagate(self, nodes):
        p1=[]
        p2=[]
        fp1=[]
        fp2=[]

        for i in range(0, (len(nodes))):
            for j in range(i, -1, -1):
                # if the node in position 'i' has an arc to 'j' 
                # or node in position 'j' has an arc to 'i'
                next_arc=self.get_next_edge(nodes, i, j)
                if next_arc == None:
                    continue
                else:
                    # check restrictions
                    if next_arc not in fp1:
                        p1.append(next_arc)
                        fp1, fp2 = self.propagate(nodes, fp1, fp2, next_arc, 2)
                    
                    elif next_arc not in fp2:
                        p2.append(next_arc)
                        fp1, fp2 = self.propagate(nodes, fp1, fp2, next_arc, 1)
        return p1, p2
    def propagate(self, nodes, fp1, fp2, current_edge, i):
        # add the current edge to the forbidden plane opposite to the plane
        # where the node has already been added
        fpi  = None
        fp3mi= None
        if i==1:
            fpi  = fp1
            fp3mi= fp2
        if i==2:
            fpi  = fp2
            fp3mi= fp1

        fpi.append(current_edge)
        
        # add all nodes from the dependency graph that crosses the current edge
        # to the corresponding forbidden plane
        for node in nodes:
            if self.check_cross(current_edge, node):
                if node not in fp3mi:
                    (fp1, fp2)=self.propagate(nodes, fp1, fp2, node, 3-i)
        
        return fp1, fp2

    def two_planar_greedy(self,nodes):    
        plane_1 = []
        plane_2 = []

        for i in range(0, (len(nodes))):
            for j in range(i, -1, -1):
                # if the node in position 'i' has an arc to 'j' 
                # or node in position 'j' has an arc to 'i'
                next_arc=self.get_next_edge(nodes, i, j)
                if next_arc == None:
                    continue

                else:
                    cross_plane_1 = False
                    cross_plane_2 = False
                    for node in plane_1:                
                        cross_plane_1=cross_plane_1 or self.check_cross(next_arc, node)
                    for node in plane_2:        
                        cross_plane_2=cross_plane_2 or self.check_cross(next_arc, node)
                    
                    if not cross_plane_1:
                        plane_1.append(next_arc)
                    elif not cross_plane_2:
                        plane_2.append(next_arc)

        # processs them separately
        return plane_1,plane_2


    def encode(self, nodes):
        if self.plane_algorithm==D_2P_GREED:
            p1_nodes, p2_nodes = self.two_planar_greedy(nodes)
        elif self.plane_algorithm==D_2P_PROP:
            p1_nodes, p2_nodes = self.two_planar_propagate(nodes)

        labels_brk=["" for e in nodes]
        labels_brk=self.encode_step(p1_nodes, labels_brk, ['>','/','\\','<'])
        labels_brk=self.encode_step(p2_nodes, labels_brk, ['>*','/*','\\*','<*'])
        
        lbls=[]
        for node in nodes:
            if node.id == 0:
                continue
            
            current = DependencyLabel(labels_brk[node.id], node.relation, self.separator)
            lbls.append(current)
        return lbls
    def encode_step(self, p, lbl_brk, brk_chars):
        for node in p:
            if node.id==0 or node.head==0:
                continue
            if node.id < node.head:
                if self.displacement:
                    lbl_brk[node.id+1]+=brk_chars[3]
                else:
                    lbl_brk[node.id]+=brk_chars[3]

                lbl_brk[node.head]+=brk_chars[2]
            else:
                if self.displacement:
                    lbl_brk[node.head+1]+=brk_chars[1]
                else:
                    lbl_brk[node.head]+=brk_chars[1]

                lbl_brk[node.id]+=brk_chars[0]
        return lbl_brk

    def decode(self, labels, postags, words):
        decoded_nodes=[ConllNode.dummy_root()]
        for l in labels:
            decoded_nodes.append(ConllNode.empty_node())
        
        # create plane stacks
        l_stack_p1=[]
        l_stack_p2=[]
        r_stack_p1=[]
        r_stack_p2=[]
        
        current_node=1
        for label, postag, word in zip(labels,postags,words):
            # join the plane signaler char with the bracket char
            brks=list(label.xi)
            temp_brks=[]
            
            for i in range(0, len(brks)):
                current_char=brks[i]
                if brks[i]=="*":
                    current_char=temp_brks.pop()+brks[i]
                temp_brks.append(current_char)
                    
            brks=temp_brks
            
            # set parameters to the node
            decoded_nodes[current_node].id = current_node
            decoded_nodes[current_node].form = word
            decoded_nodes[current_node].upos = postag
            decoded_nodes[current_node].relation = label.li
            
            # fill the relation using brks
            for char in brks:
                if char == "<":
                    node_id=current_node + (-1 if self.displacement else 0)
                    r_stack_p1.append((node_id,char))
                
                if char == "\\":
                    head_id = r_stack_p1.pop()[0] if len(r_stack_p1)>0 else 0
                    decoded_nodes[head_id].head=current_node
                
                if char =="/":
                    node_id=current_node + (-1 if self.displacement else 0)
                    l_stack_p1.append((node_id,char))

                if char == ">":
                    head_id = l_stack_p1.pop()[0] if len(l_stack_p1)>0 else 0
                    decoded_nodes[current_node].head=head_id

                if char == "<*":
                    node_id=current_node + (-1 if self.displacement else 0)
                    r_stack_p2.append((node_id,char))
                
                if char == "\\*":
                    head_id = r_stack_p2.pop()[0] if len(r_stack_p2)>0 else 0
                    decoded_nodes[head_id].head=current_node
                
                if char =="/*":
                    node_id=current_node + (-1 if self.displacement else 0)
                    l_stack_p2.append((node_id,char))

                if char == ">*":
                    head_id = l_stack_p2.pop()[0] if len(l_stack_p2)>0 else 0
                    decoded_nodes[current_node].head=head_id
            
            current_node+=1

        return decoded_nodes[1:]    
