from conllu import parse_tree_incr
import itertools

# encoding type constants
D_ABSOLUTE_ENCODING = 'ABS'
D_RELATIVE_ENCODING = 'REL'
D_POS_ENCODING = 'POS'
D_BRACKET_ENCODING = 'BRK'
D_BRACKET_ENCODING_2P = 'BRK_2P'
D_2P_GREED = '2P_GRD'
D_2P_PROP = '2P_PRP'


class dependency_graph_node:
    # class for the nodes of the dependency graph obtained
    # from the sentence
    # id: position of the word in the sentence
    # text: word
    # head: number of the word this depends to
    # pos: postag of the word
    # relation: dependency relation between id and head
    def __init__(self, wid, text, head, pos, relation):
        self.id = int(wid)
        self.text = text
        self.head = int(head)
        self.pos = pos
        self.relation = relation
class encoded_dependency_label:
    # class for the encoded dependency label
    # stores the value of xi, li and the encoding type used
    def __init__(self, encoding_type, xi, li):
        self.encoding_type = encoding_type
        self.xi = xi
        self.li = li

##############################

class dependency_encoder:
    def __init__(self, encoding_type):
        self.encoder = encoding_type
    
    def encode(self, nodes):
        return self.encoder.encode(nodes)

class d_absolute_encoder:
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            current = encoded_dependency_label(D_ABSOLUTE_ENCODING, node.head, node.relation)
            encoded_labels.append(current)

        return encoded_labels
class d_relative_encoder:
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            current = encoded_dependency_label(D_RELATIVE_ENCODING, node.head-node.id, node.relation)
            encoded_labels.append(current)

        return encoded_labels
class d_pos_encoder:
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            # create the (pi, oi) tuple
            
            # oi: PoS tag of the word in the head position            
            oi = nodes[max(node.head,0)].pos
            
            # pi: number of oi found until reach the head position
            #     left -> netative ;; right -> positive

            pi=0

            # move to the head
            step = 1
            head = node.head
            nid = node.id
            
            # change the step according to moving left or right
            if (node.id > node.head):
                step = -step
            
            head+=step
            for i in range(node.id, head, step):
                if oi == nodes[i].pos:
                    pi+=step

            current=encoded_dependency_label(D_POS_ENCODING, (pi, oi), node.relation)
            encoded_labels.append(current)
        
        return encoded_labels
class d_brk_encoder:
    def __init__(self, displacement):
        self.displacement = displacement
    
    def encode(self, nodes):
        labels_brk=["" for e in nodes]
        lbls=[]
        
        for node in nodes:
            # dont encode anything on root or dummy node
            if node.id==0 or node.head==0:
                continue
            
            # arrow incoming from right
            # head is RIGHT to ID
            if node.id < node.head:
                # if i have a incoming arrow from right: 
                #       < at node.id + (displacement?1:0)
                #       \ at head
                if self.displacement:
                    labels_brk[node.id+1]+='<'
                else:
                    labels_brk[node.id]+='<'

                labels_brk[node.head]+='\\'
            
            # arrow incoming from left
            # head is LEFT to ID
            else:
                # if i have a incoming arrow from left:
                #       / at node.id + (displacement?1:0)
                #       > at head
                if self.displacement:
                    labels_brk[node.head+1]+='/'
                else:
                    labels_brk[node.head]+='/'

                labels_brk[node.id]+='>'
        
        for node in nodes:
            current = encoded_dependency_label(D_BRACKET_ENCODING, labels_brk[node.id], node.relation)
            lbls.append(current)

        return lbls
class d_brk_2p_encoder:
    def __init__(self, plane_algorithm, displacement):
        self.plane_algorithm = plane_algorithm
        self.displacement = displacement

    # auxiliar functions
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

    # plane split propagate
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

    # plane split greed
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

    # encoding
    def encode(self, nodes):
        # split the dependency graph nodes in two planes
        if self.plane_algorithm==D_2P_GREED:
            p1_nodes, p2_nodes = self.two_planar_greedy(nodes)
        elif self.plane_algorithm==D_2P_PROP:
            p1_nodes, p2_nodes = self.two_planar_propagate(nodes)

        labels_brk=["" for e in nodes]
        labels_brk=self.enc_p2_step(p1_nodes, labels_brk, ['>','/','\\','<'])
        labels_brk=self.enc_p2_step(p2_nodes, labels_brk, ['>*','/*','\\*','<*'])
        
        lbls=[]
        for node in nodes:
            current = encoded_dependency_label(D_BRACKET_ENCODING, labels_brk[node.id], node.relation)
            lbls.append(current)
        return lbls

    def enc_p2_step(self, p, lbl_brk, brk_chars):
        for node in p:
            # dont encode anything on root or dummy node
            if node.id==0 or node.head==0:
                continue
            # left dependency (arrow comming from right)
            if node.id < node.head:
                if self.displacement:
                    lbl_brk[node.id+1]+=brk_chars[3]
                else:
                    lbl_brk[node.id]+=brk_chars[3]

                lbl_brk[node.head]+=brk_chars[2]
            # right dependency (arrow comming from left)
            else:
                if self.displacement:
                    lbl_brk[node.head+1]+=brk_chars[1]
                else:
                    lbl_brk[node.head]+=brk_chars[1]

                lbl_brk[node.id]+=brk_chars[0]
        return lbl_brk

##############################

class dependency_decoder:
    def __init__(self, decoder):
        self.decoder = decoder

    def decode(self, labels):
        return self.decoder.decode(labels)

class d_absolute_decoder:
    def decode(self, labels):
        decoded_nodes = []
        i = 1
        for label in labels:
            decoded_nodes.append(dependency_graph_node(i, "", label.xi, "", label.li))
            i+=1

        return decoded_nodes
class d_relative_decoder:
    def decode(self, labels):
        decoded_nodes = []
        i = 1
        for label in labels:
            decoded_nodes.append(dependency_graph_node(i, "", label.xi+i, "", label.li))
            i+=1
        
        return decoded_nodes
class d_pos_decoder:
    def __init__(self, pos_tags):
        self.pos_tags=pos_tags

    def decode(self, labels):
        decoded_nodes = []
        i=0
        for label in labels:
            # get the (pi, oi) tuple
            # oi: PoS tag of the word in the head position
            # pi: number of oi found until reach the head position
            pi,oi=label.xi 

            if (oi=='ROOT'):
                i+=1
                decoded_nodes.append(dependency_graph_node(i+1, "", 0, "", label.li))
                continue

            # store the value of pi (number of oi found) to substract it
            target_pi = pi

            # create the step and the stop point 
            step = 1
            stop_point = len(self.pos_tags)-i
            
            if (pi<0):
                step = -1
                stop_point = 0

            # iterate over the postags until find the one matching
            # we iterate starting at the word and in the direction 
            # of the head, depending if it is positive or negative
            # at the end of this loop j will have the position 
            # of the head

            for j in range (i, stop_point, step):                  
                if (oi==self.pos_tags[j]):
                    target_pi-=step
                if (target_pi==0):
                    break       
                
            decoded_nodes.append(dependency_graph_node(i+1, "", j+1, "", label.li))

            i+=1
        
        return decoded_nodes
class d_brk_decoder:
    def __init__(self, displacement):
        self.displacement=displacement

    def decode(self, labels):
        # decoding: each opening bracket closes with the first encountered
        # can decode non-projective trees where the arcs cross in different directions
        # cant encode non-projective trees where the arcs cross in the same direction
        decoded_nodes=[0 for l in labels]
        # stack formed by tuples ('brk_char', 'id', 'rel')
        # char : bracket of the label
        # id : node that put the char
        # l_stack -> dependencies where head < id (head is more left than id) (arrow go from right towards left)
        # r_stack -> dependencies here head > id  (head is more right than id) (arrow go from left towards right)
        l_stack = []
        r_stack = []
        
        current_node = 0

        for label in labels:
            brks=list(label.xi)
                        
            # create a the node
            decoded_nodes[current_node]=dependency_graph_node(current_node, "", 0, "", label.li)
        
            # fill the relation using brks
            for char in brks:
                if char == "<":
                    #  current_node-1 has incoming arc from right
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id = current_node
                    r_stack.append((node_id,char))
                if char == "\\":
                    head_id = r_stack.pop()[0]
                    decoded_nodes[head_id].head=current_node
                
                
                if char =="/":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id = current_node
                    l_stack.append((node_id,char))
                if char == ">":
                    head_id = l_stack.pop()[0]
                    decoded_nodes[current_node].head=head_id
            
            current_node+=1

        return decoded_nodes        
class d_brk_2p_decoder:
    def __init__(self, displacement):
        self.displacement=displacement
    
    def decode(self, labels):
        decoded_nodes=[None for l in labels]
        
        # create plane stacks
        l_stack_p1=[]
        l_stack_p2=[]
        r_stack_p1=[]
        r_stack_p2=[]
        
        current_node=0

        for label in labels:
            # join the plane signaler char with the bracket char
            brks=list(label.xi)
            temp_brks=[]
            
            for i in range(0, len(brks)):
                current_char=brks[i]
                if brks[i]=="*":
                    current_char=temp_brks.pop()+brks[i]
                temp_brks.append(current_char)
                    
            brks=temp_brks
            
            # create a the node
            decoded_nodes[current_node]=dependency_graph_node(current_node, "", 0, "", label.li)
        
            # fill the relation using brks
            for char in brks:
                if char == "<":
                    # current_node-1 has incoming arc from right
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node
                    r_stack_p1.append((node_id,char))
                if char == "\\":
                    # current_node has outgoing arc towards left
                    head_id = r_stack_p1.pop()[0]
                    decoded_nodes[head_id].head=current_node
                
                
                if char =="/":
                    # current_node-1 has outgoing arc towards right
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node
                    l_stack_p1.append((node_id,char))
                if char == ">":
                    # current_node has incoming arc from left
                    head_id = l_stack_p1.pop()[0]
                    decoded_nodes[current_node].head=head_id

                    
                if char == "<*":
                    # current_node-1 has incoming arc from right
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node
                    r_stack_p2.append((node_id,char))
                if char == "\\*":
                    # current_node has outgoing arc towards left
                    head_id = r_stack_p2.pop()[0]
                    decoded_nodes[head_id].head=current_node
                
                
                if char =="/*":
                    # current_node-1 has outgoing arc towards right
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node
                    l_stack_p2.append((node_id,char))
                if char == ">*":
                    # current_node has incoming arc from left
                    head_id = l_stack_p2.pop()[0]
                    decoded_nodes[current_node].head=head_id
            
            current_node+=1
        
        return decoded_nodes

##############################

# parses a conllu file and returns dependency_graph_node
def parse_conllu(token_tree):
    nodes = []
    pos_tags = []
    # add dummy root
    nodes.append(dependency_graph_node(0, 'ROOT', 0, 'ROOT', 'ROOT'))

    # serialize the data from the collu file
    data = token_tree.serialize().split('\n')
    # remove the metadata lines
    data = data[2:]
    for line in data:
        # split the line in tabs
        line = line.split('\t')

        # check if empty line
        if (len(line)<=1):
            continue

        # extract the useful data
        word_id=line[0]
        text=line[1]
        head=line[6]
        pos=line[3]
        rel=line[7]

        nodes.append(dependency_graph_node(word_id, text, head, pos, rel))
        pos_tags.append((pos,text))
    return nodes,pos_tags

# given a tree encodes it and decodes and checks if it is the same
def test_file(filepath,e,d):
    data_file = open(filepath, "r", encoding="utf-8")
    
    i=0
    for token_tree in parse_tree_incr(data_file):
        r = test_single(token_tree,e,d)
        if not r:
            print("[*] Error at",i)
            break
        i+=1
def test_single(tt,e,d):
    nodes,pos_tags=parse_conllu(tt)
    encoded_labels=e.encode(nodes)
    decoded_nodes=d.decode(encoded_labels)

    return nodes == decoded_nodes

def linearize_single(tt, e):
    nodes,pos_tags = parse_conllu(tt)
    encoded_labels = e.encode(nodes)

    # linearized tree will be shaped like
    # (WORD  POSTAG  LABEL)
    lt=[]
    lt.append(('-BOS-','-BOS-','-BOS-'))
    for l, p in zip(encoded_labels, pos_tags):
        lt.append((str(l.li)+"_"+str(l.xi), p[1], p[0]))
    lt.append(('-EOS-','-EOS-','-EOS-'))
    return lt
def linearize_dependencies(in_path, out_path, encoder):
    f_in=open(in_path)
    f_out=open(out_path,"w+")
    
    for d_tree in parse_tree_incr(f_in):
        linearized_tree = linearize_single(d_tree, encoder)
        for label in linearized_tree:
            f_out.write(u"\t".join([label[2],label[1],label[0]])+u"\n")
        f_out.write("\n")


    
