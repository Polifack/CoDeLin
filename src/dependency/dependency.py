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

##############################################################################
##############################################################################
##############################################################################

class dependency_encoder:
    def __init__(self, encoding_type):
        self.encoder = encoding_type
    
    def encode(self, nodes):
        return self.encoder.encode(nodes)

class dependency_absolute_encoder:
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            current = encoded_dependency_label(D_ABSOLUTE_ENCODING, node.head, node.relation)
            encoded_labels.append(current)

        return encoded_labels

class dependency_relative_encoder:
    def encode(self, nodes):
        encoded_labels = []
        for node in nodes:
            current = encoded_dependency_label(D_RELATIVE_ENCODING, node.head-node.id, node.relation)
            encoded_labels.append(current)

        return encoded_labels

class dependency_pos_encoder:
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

class dependency_brk_encoder:
    def __init__(self, displacement):
        self.displacement = displacement
    
    def encode(self, nodes):
        labels_brk=["" for e in nodes]
        lbls=[]
        
        for node in nodes:
            if node.head==0:
                continue
            # left dependency (arrow comming from right)
            if node.id<node.head:
                labels_brk[node.id]+='<'
                
                # check if we are encoding with displacement or not
                if (self.displacement):
                    brk_pos=node.head-1
                else:
                    brk_pos=node.head

                labels_brk[brk_pos]+='\\'
            # right dependency (arrow comming from left)
            else:
                labels_brk[node.head]+='/'

                # check if we are encoding with displacement or not
                if (self.displacement):
                    brk_pos=node.id-1
                else:
                    brk_pos=node.id

                labels_brk[brk_pos]+='>'
        
        for node in nodes:
            current = encoded_dependency_label(D_BRACKET_ENCODING, labels_brk[node.id-1], node.relation)
            lbls.append(current)

        return lbls

class dependency_brk_2p_encoder:
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
        
        id_inside = (node.head < next_arc.id < node.id)
        if node.head == next_arc.head and id_inside:
             return False
        else:
            head_inside = (node.head < next_arc.head < node.id)
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
                        
                        # recompute restriction set
                        fp1, fp2 = self.propagate(nodes, fp1, fp2, next_arc, 2)
                    
                    elif next_arc not in fp2:
                        p2.append(next_arc)
                        
                        # recompute restriction set
                        fp1, fp2 = self.propagate(nodes, fp1, fp2, next_arc, 1)
        return p1, p2

    def propagate(self, nodes, fp1, fp2, current_edge, i):
        # add the current edge to the forbidden plane opposite to the plane
        # where the node has already been added
        if i==1:
            fp1.append(current_edge)
        if i==2:
            fp2.append(current_edge)
        
        # add all nodes from the dependency graph that crosses the current edge
        # to the corresponding forbidden plane
        for node in nodes:
            if self.check_cross(current_edge, node):
                if i==2 and node not in fp1:
                    (fp1, fp2)=self.propagate(nodes, fp1, fp2, node, 1)
                if i==1 and node not in fp2:
                    (fp1, fp2)=self.propagate(nodes, fp1, fp2, node, 2)
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
                        cross_plane_1=self.check_cross(next_arc, node)
                        
                    for node in plane_2:               
                        cross_plane_2=self.check_cross(next_arc, node)
                    
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

        lbl_brk=["" for e in range(0, len(nodes))]
        lbl_brk=self.enc_p2_step(p1_nodes, lbl_brk,['>','/','\\','<'])
        lbl_brk=self.enc_p2_step(p2_nodes, lbl_brk,['>*','/*','\\*','<*'])
        
        lbls=[]
        for node in nodes:
            current = encoded_dependency_label(D_BRACKET_ENCODING_2P, lbl_brk[node.id-1], node.relation)
            lbls.append(current)
        return lbls

    def enc_p2_step(self, p, lbl_brk, brk_chars):
        for node in p:
            if node.head==0:
                continue
            # left dependency (arrow comming from right)
            if node.id<node.head:
                lbl_brk[node.id]+=brk_chars[3]

                if (self.displacement):
                    brk_pos=node.head-1
                else:
                    brk_pos=node.head
                
                lbl_brk[brk_pos]+=brk_chars[2]
            # right dependency (arrow comming from left)
            else:
                lbl_brk[node.head]+=brk_chars[1]
                
                if (self.displacement):
                    brk_pos=node.id-1
                else:
                    brk_pos=node.id
                
                lbl_brk[brk_pos]+=brk_chars[0]
        return lbl_brk

##############################################################################
##############################################################################
##############################################################################

class dependency_decoder:
    def __init__(self, decoder):
        self.decoder = decoder

    def decode(self, labels):
        return self.decoder.decode(labels)

class dependency_absolute_decoder:
    def decode(self, labels):
        decoded_nodes = []
        i = 1
        for label in labels:
            decoded_nodes.append(dependency_graph_node(i, "", label.xi, "", label.li))
            i+=1

        return decoded_nodes

class dependency_relative_decoder:
    def decode(self, labels):
        decoded_nodes = []
        i = 1
        for label in labels:
            decoded_nodes.append(dependency_graph_node(i, "", label.xi+i, "", label.li))
            i+=1
        
        return decoded_nodes

class dependency_pos_decoder:
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

class dependency_brk_decoder:
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
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node

                    node_rel = labels[node_id].li
                    r_stack.append((node_id,char))

                    decoded_nodes[node_id]=dependency_graph_node(node_id, "", -1, "", node_rel)
                if char =="/":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node
                    
                    l_stack.append((node_id,char))
                if char == "\\":
                    # if (existe en el stack algun '<' (esto es, hay una apertura), popearlo)
                    head_id = r_stack.pop()[0]
                    decoded_nodes[head_id].head=current_node
                if char == ">":
                    # word i tiene arco entrante desde la izquierda
                    # if (existe en el stack algun '/' (esto es, hay una apertura), popearlo)
                    head_id = l_stack.pop()[0]

                    # adding 1 to node_id because labels start in 1 and not in 0
                    decoded_nodes[current_node]=dependency_graph_node(current_node, "", head_id, "", label.li)
            
            current_node+=1

        return decoded_nodes        

class dependency_brk_2p_decoder:
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
                    

            # create a the node
            decoded_nodes[current_node]=dependency_graph_node(current_node, "", 0, "", label.li)
        
            # fill the relation using brks
            for char in brks:
                if char == "<":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node

                    node_rel = labels[node_id].li
                    r_stack_p1.append((node_id,char))

                    decoded_nodes[node_id]=dependency_graph_node(node_id, "", -1, "", node_rel)
                if char =="/":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node

                    l_stack_p1.append((node_id,char))
                if char == "\\":
                    # if (existe en el stack algun '<' (esto es, hay una apertura), popearlo)
                    head_id = r_stack_p1.pop()[0]
                    decoded_nodes[head_id].head=current_node
                if char == ">":
                    # word i tiene arco entrante desde la izquierda
                    # if (existe en el stack algun '/' (esto es, hay una apertura), popearlo)
                    head_id = l_stack_p1.pop()[0]

                    # adding 1 to node_id because labels start in 1 and not in 0
                    decoded_nodes[current_node]=dependency_graph_node(current_node, "", head_id, "", label.li)

                    
                if char == "<*":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node

                    node_rel = labels[node_id].li
                    r_stack_p2.append((node_id,char))

                    decoded_nodes[node_id]=dependency_graph_node(node_id, "", -1, "", node_rel)
                if char =="/*":
                    if self.displacement:
                        node_id = current_node-1
                    else:
                        node_id=current_node

                    l_stack_p2.append((node_id,char))
                if char == "\\*":
                    # if (existe en el stack algun '<' (esto es, hay una apertura), popearlo)
                    head_id = r_stack_p2.pop()[0]
                    decoded_nodes[head_id].head=current_node
                if char == ">*":
                    # word i tiene arco entrante desde la izquierda
                    # if (existe en el stack algun '/' (esto es, hay una apertura), popearlo)
                    head_id = l_stack_p2.pop()[0]

                    # adding 1 to node_id because labels start in 1 and not in 0
                    decoded_nodes[current_node]=dependency_graph_node(current_node, "", head_id, "", label.li)
            
            current_node+=1
        
        return decoded_nodes

##############################################################################
##############################################################################
##############################################################################

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

def test_treebank(filepath):
    data_file = open(filepath, "r", encoding="utf-8")
    for token_tree in parse_tree_incr(data_file):
        test_single(token_tree)

def test_single(tt):
    nodes,pos_tags=parse_conllu(tt)
    
    print("[*] Dependency graph:")
    for node in nodes:
        print(node.id, node.head, node.relation)
    
    displacement=True
    
    e=dependency_brk_2p_encoder(D_2P_GREED, displacement)
    #e=dependency_brk_encoder(displacement)
    encoded_labels=e.encode(nodes)
    
    print("[*] Encoded labels:")
    for label in encoded_labels:
        print('xi:',label.xi,'li:',label.li)
    
    d=dependency_brk_2p_decoder(displacement)
    #d=dependency_brk_decoder(displacement)
    decoded_nodes=d.decode(encoded_labels)
    
    
    for node, decoded_node in zip(nodes,decoded_nodes):
        if not (node.id==decoded_node.id and node.head==decoded_node.head):
            print("Error at",node.id)
            break

    print("[*] Decoded dependency graph:")
    for decoded_node in decoded_nodes:
        print(decoded_node.id, decoded_node.head, decoded_node.relation)


if __name__=="__main__":
    #data_file=open("/home/poli/TFG/test/dependencies/UD_Spanish-GSD/es_gsd-ud-dev.conllu")
    #data_file=open("/home/poli/TFG/test/dependencies/proj.conllu")
    data_file=open("/home/poli/TFG/test/dependencies/temp.conllu")
    #sid=79
    sid=0
    #test_treebank("/home/poli/TFG/test/dependencies/UD_Spanish-GSD/es_gsd-ud-dev.conllu")
    
    tt=parse_tree_incr(data_file)
    tt=next(itertools.islice(tt, sid, None))
    test_single(tt)



    
