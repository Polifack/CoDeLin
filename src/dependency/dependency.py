from conllu import parse_tree_incr


# encoding type constants
D_ABSOLUTE_ENCODING = 'ABS'
C_RELATIVE_ENCODING = 'REL'
D_POS_ENCODING = 'POS'
D_BRACKET_ENCODING = 'BRA'

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
        # return the encoded labels without the dummy root label
        return self.encoder.encode(nodes)[1:]

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
            current = encoded_dependency_label(C_RELATIVE_ENCODING, node.head-node.id, node.relation)
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

##############################################################################
##############################################################################
##############################################################################

class dependency_decoder:
    def __init__(self, pos_tags):
        # store the pos_tags in case of needed
        self.pos_tags = pos_tags

    def decode(self, labels):
        encoding_type = labels[0].encoding_type
        
        if (encoding_type==D_ABSOLUTE_ENCODING): 
            return dependency_absolute_decoder().decode(labels)
        elif (encoding_type==C_RELATIVE_ENCODING):
            return dependency_relative_decoder().decode(labels)
        elif (encoding_type==D_POS_ENCODING):
            return dependency_pos_decoder().decode(labels,self.pos_tags)

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
    def decode(self, labels, pos_tags):
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
            stop_point = len(pos_tags)-i
            
            if (pi<0):
                step = -1
                stop_point = 0

            # iterate over the postags until find the one matching
            # we iterate starting at the word and in the direction 
            # of the head, depending if it is positive or negative
            # at the end of this loop j will have the position 
            # of the head

            for j in range (i, stop_point, step):                  
                if (oi==pos_tags[j]):
                    target_pi-=step
                if (target_pi==0):
                    break       
                
            decoded_nodes.append(dependency_graph_node(i+1, "", j+1, "", label.li))

            i+=1
        
        return decoded_nodes


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
        pos_tags.append(pos)
    return nodes,pos_tags

def test_treebank(filepath, encoder):
    data_file = open(filepath, "r", encoding="utf-8")
    for token_tree in parse_tree_incr(data_file):
        nodes, pos_tags = parse_conllu(token_tree)
        
        print("[*] Dependency graph:")
        for node in nodes:
            print(node.id, node.head, node.relation)

        encoded_labels = encoder.encode(nodes)
        
        print("[*] Encoded labels:")
        for label in encoded_labels:
            print('xi:',label.xi,'li:',label.li)

        decoder = dependency_decoder(pos_tags)
        decoded_nodes = decoder.decode(encoded_labels)

        print("[*] Decoded dependency graph:")
        for node in decoded_nodes:
            print(node.id, node.text, node.head, node.relation)
