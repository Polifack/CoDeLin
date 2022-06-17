from conllu import parse_tree_incr
import itertools
import stanza

# encoding type constants
D_ABSOLUTE_ENCODING = 'ABS'
D_RELATIVE_ENCODING = 'REL'
D_POS_ENCODING = 'POS'
D_BRACKET_ENCODING = 'BRK'
D_BRACKET_ENCODING_2P = 'BRK_2P'

D_2P_GREED = 'GREED'
D_2P_PROP = 'PROPAGATE'

D_BOS = '-BOS-'
D_EOS = '-EOS-'

D_EMPTYREL = "-NOREL-"
D_POSROOT = "-ROOT-"

class ConllNode:
    def __init__(self, wid, form, lemma, upos, xpos, feats, head, deprel, deps, misc):
        self.id = wid                           # word id
        
        self.form = form if form else "_"       # word 
        self.lemma = lemma if lemma else "_"    # word lemma/stem
        self.upos = upos if upos else "_"       # universal postag
        self.xpos = xpos if xpos else "_"       # language_specific postag
        self.feats = feats if feats else "_"    # morphological features
        
        self.head = head                        # id of the word that depends on
        self.relation = deprel                  # type of relation with head

        self.deps = deps if deps else "_"       # enhanced dependency graph
        self.misc = misc if misc else "_"       # miscelaneous data
    
    def __repr__(self):
        return '\t'.join(str(e) for e in list(self.__dict__.values()))+'\n'

    @staticmethod
    def from_string(conll_str):
        wid,form,lemma,upos,xpos,feats,head,deprel,deps,misc = conll_str.split('\t')
        return ConllNode(int(wid), form, lemma, upos, xpos, feats, int(head), deprel, deps, misc)

    @staticmethod
    def dummy_root():
        return ConllNode(0, D_POSROOT, None, D_POSROOT, None, None, 0, D_EMPTYREL, None, None)
    
    @staticmethod
    def empty_node():
        return ConllNode(0, None, None, None, None, None, 0, None, None, None)

class DependencyLabel:
    def __init__(self, xi, li, sp):
        self.separator = sp

        self.xi = xi    # dependency relation
        self.li = li    # encoding

    def __repr__(self):
        return f'{self.xi}{self.separator}{self.li}'

    @staticmethod
    def from_string(lbl_str, sep):
        xi, li = lbl_str.split(sep)
        return DependencyLabel(xi, li, sep)

class DependencyEncoder:
    def __init__(self, encoding, separator, displacement, planar_alg):
        self.separator = separator
        self.displacement = displacement
        self.plane_algorithm = planar_alg
        self.encoding = encoding
    
    def encode(self, nodes):
        encoded_labels = None

        if self.encoding == D_ABSOLUTE_ENCODING:
            return self.encode_abs(nodes)
        
        elif self.encoding == D_RELATIVE_ENCODING:
            return self.encode_rel(nodes)

        elif self.encoding == D_POS_ENCODING:
            return self.encode_pos(nodes)

        elif self.encoding == D_BRACKET_ENCODING:
            return self.encode_brk(nodes)

        elif self.encoding == D_BRACKET_ENCODING_2P:
            return self.encode_brk_2p(nodes)

    def encode_abs(self, nodes):
        encoded_labels = []
        for node in nodes:
            # skip dummy root
            if node.id == 0:
                continue

            li = node.relation

            # xi computation
            xi = node.head
            
            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels

    def encode_rel(self, nodes):
        encoded_labels = []
        for node in nodes:
            # skip dummy root
            if node.id == 0:
                continue

            li = node.relation

            # xi computation
            xi = str(int(node.head)-int(node.id))
            
            current = DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)

        return encoded_labels

    def encode_pos(self, nodes):
        encoded_labels = []

        for node in nodes:
            # skip dummy root
            if node.id == 0:
                continue

            li = node.relation

            # xi computation
            node_head = int(node.head)
            node_id = int(node.id)

            # xi computation
            oi = nodes[node_head].upos
            pi = 0

            step = 1 if node_id < node_head else -1

            for i in range(node_id, node_head+step, step):
                if oi == nodes[i].upos:
                    pi += step

            xi = str(pi)+"--"+oi

            current=DependencyLabel(xi, li, self.separator)
            encoded_labels.append(current)
        
        return encoded_labels


    #### REFACTOR CODE

    def encode_brk(self, nodes):
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

    ## 2PLANAR BRK

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
    def encode_brk_2p(self, nodes):
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
            if node.id == 0:
                continue
            
            current = DependencyLabel(labels_brk[node.id], node.relation, self.separator)
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

class DependencyDecoder:
    def __init__(self, encoding, separator, displacement=False):
        self.encoding = encoding
        self.displacement = displacement
        self.separator = separator
        
    ## Postprocessing
    def f_check_roots(self, nodes):
        check_rel = False
        fix_rel = False
        default_root = 1
        
        # find the root
        root = None
        for node in nodes:
            if not check_rel and node.head == 0:
                root = node
                break
            
            if check_rel and node.rel == 'root':
                root = node
                break

       # if no root found pick the first one
       # this should be configurable
        if (root == None):
            root = nodes[default_root]
        
        # sanity check
        root.head = 0
        if fix_rel:
            root.rel = 'root'

        # remove -1 nodes from other steps
        for node in nodes:
            if node.head <= 0 and (node!=root):
                node.head = root.id
 
    def check_loops(self, nodes):
        # complexity huge; can it be improved?
        for node in nodes:
            visited = []
            while (node.head != 0) and (node.head!=-1):
                if node in visited:
                    node.head = -1
                else:
                    visited.append(node)
                    node = nodes[node.head-1]

    def check_valid_nodes(self, nodes):
        for node in nodes:
            # if a node has head outside range of nodes
            # set head at root
            if int(node.head) < 0:
                node.head = -1
            elif int(node.head) > (nodes[-1].id):
                node.head = -1

    ## Main function
    def decode(self, labels, postags,words):
        
        decoded_nodes = None

        if self.encoding == D_ABSOLUTE_ENCODING:
            decoded_nodes = self.decode_abs(labels, postags, words)
        if self.encoding == D_RELATIVE_ENCODING:
            decoded_nodes = self.decode_rel(labels, postags, words)
        if self.encoding == D_POS_ENCODING:
            decoded_nodes = self.decode_pos(labels, postags, words)
        if self.encoding == D_BRACKET_ENCODING:
            decoded_nodes = self.decode_brk(labels, postags, words)
        if self.encoding == D_BRACKET_ENCODING_2P:
            decoded_nodes = self.decode_brk_2p(labels, postags, words)

        self.check_valid_nodes(decoded_nodes)
        self.check_loops(decoded_nodes)
        self.f_check_roots(decoded_nodes)
        return decoded_nodes
    
    ## Algorithms
    def decode_abs(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]

        i = 1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)
            
            node.relation = label.li
            node.head = label.xi

            decoded_nodes.append(node)
            i+=1
        return decoded_nodes[:1]

    def decode_rel(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]
        
        i = 1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)

            node.relation = label.li
            node.head = int(label.xi)+node.id

            decoded_nodes.append(node)
            i+=1
        
        return decoded_nodes[:1]

    def decode_pos(self, labels, postags, words):
        decoded_nodes = [ConllNode.dummy_root()]
        
        i=1
        for label, postag, word in zip(labels, postags, words):
            node = ConllNode(i, word, None, postag, None, None, None, None, None, None)

            node.relation = label.li
            

            pi, oi = label.xi.split('--')            
            pi = int(pi)

            # ROOT is a special case
            if (oi==D_POSROOT):
                node.head = 0
                decoded_nodes.append(node)
                
                i+=1
                continue

            # store the value of pi (number of oi found) to substract it
            target_pi = pi

            # create the step and the stop point 
            step = 1 if pi > 0 else -1
            stop_point = (len(postags)+1) if pi > 0 else 0

            for j in range (node.id, stop_point, step):                  
                if (oi == postags[j-1]):
                    target_pi -= step
                
                if (target_pi==0):
                    break       
            
            node.head = j
            
            decoded_nodes.append(node)
            i+=1
        
        return decoded_nodes[1:]

    def decode_brk(self, labels, postags, words):
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
                    r_stack.append((node_id,char))

                if char == "\\":
                    head_id = r_stack.pop()[0] if len(r_stack)>0 else 0
                    decoded_nodes[head_id].head=current_node
                
                if char =="/":
                    node_id = current_node + (-1 if self.displacement else 0)
                    l_stack.append((node_id,char))

                if char == ">":
                    head_id = l_stack.pop()[0] if len(l_stack)>0 else 0
                    decoded_nodes[current_node].head=head_id
            
            current_node+=1

        return decoded_nodes[1:]

    def decode_brk_2p(self, labels, postags, words):
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

# parses a conllu file and returns ConllNode
def parse_conllu(token_tree, nlp=None):
    nodes = []
    postags = []
    words = []
    
    # add dummy root
    nodes.append(ConllNode.dummy_root())

    # serialize the data from the collu file
    data = token_tree.serialize().split('\n')

    # get the sentence, dependency data and 
    # if desired predict the postags

    dependency_start_idx=0
    for line in data:
        if line[0]!="#":
            break
        if "# text" in line:
            sentence=line.split("# text = ")[1]
        dependency_start_idx+=1
    
    data = data[dependency_start_idx:]

    if nlp is not None:
        
        predicted_postags=[]
        doc = nlp(sentence)
        
        for element in doc.sentences:
            for word in element.words:
                predicted_postags.append(word.upos)

        for line in data:
            # check if empty line or comment
            if (len(line)<=1) or line[0] == "#":
                continue
            
            conll_node = ConllNode.from_string(line)
            nodes.append(conll_node)
            pos_tags.append(conll_node.upos)
            words.append(conll_node.form)

    else:
        for line in data:
            # check if empty line
            if (len(line)<=1)or line[0] == "#":
                continue
            
            conll_node = ConllNode.from_string(line)
            nodes.append(conll_node)
            postags.append(conll_node.upos)
            words.append(conll_node.form)
    
    return nodes, postags, words

def encode_dependencies(in_path, out_path, separator, encoding_type, displacement, planar_alg, postags, lang, features):
    # create encoder
    encoder = DependencyEncoder(encoding_type, separator, displacement, planar_alg)

    # open files
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    # optional part to linearize tree using predicted pos_tags
    nlp = None
    if postags:
        # stanza.download(lang=lang, model_dir="./stanza_resources")
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos', model_dir="./stanza_resources")
    
    # optinal part to include features in output file
    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1


    tree_counter = 0
    label_counter = 0
    
    for d_tree in parse_tree_incr(f_in):
    
        nodes, postags, words = parse_conllu(d_tree, nlp)
        encoded_labels = encoder.encode(nodes)

        linearized_tree=[]
        linearized_tree.append(u" ".join(([D_BOS] * (3 + (1+len(features) if features else 0)))))
        
        for n, l, p, w in zip(nodes, encoded_labels, postags, words):
            output_line = [w, p]

            # check for additional features
            if features:
                output_line.append(n.lemma)
                f_list = ["_"] * len(features)
                af = n.feats.split("|")
                for element in af:
                    key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                    if key in f_idx_dict.keys():
                        f_list[f_idx_dict[key]] = value
                
                # append the additional elements or the placehodler
                for element in f_list:
                    output_line.append(element)

            output_line.append(str(l))

            linearized_tree.append(u" ".join(output_line))
        linearized_tree.append(u" ".join(([D_EOS] * (3 + (1+len(features) if features else 0)))))
    
        for row in linearized_tree:
            label_counter+=1
            f_out.write(row+'\n')
        f_out.write("\n")
        tree_counter+=1
    
    return tree_counter, label_counter

def decode_dependencies(in_path, out_path, separator, encoding_type, displacement, postags, lang):
    # create decoder
    decoder = DependencyDecoder(encoding_type, separator, displacement=displacement)

    # open files
    f_in=open(in_path)
    f_out=open(out_path,"w+")

    # start stanza for pos prediction
    # note that 'en' must be a language variable 
    #stanza.download(lang='en', model_dir="./stanza_resources")
    nlp = stanza.Pipeline(lang='en', processors='tokenize,pos', model_dir="./stanza_resources")

    token_list_counter=0
    labels_counter=0

    current_labels = []
    current_words = []
    current_postags = []
    
    for line in f_in:    
        if D_BOS in line:
            current_labels=[]
            current_words=[]
            current_postags=[]

            continue

        if D_EOS in line:
            decoded_conllu = decoder.decode(current_labels, current_postags, current_words)
            for l in decoded_conllu:
                f_out.write(str(l))
            f_out.write('\n')

            token_list_counter+=1
            continue

        labels_counter+=1

        line = line.replace('\n','')
        split_line = line.split(' ')
        
        if len(split_line) == 3:
            word, postag, lbl_str = split_line
        
        elif len(split_line) == 2:
            word, lbl_str = split_line
            postag = ""

            if postags:
                print("[*] Adding postags predicted")

        current_labels.append(DependencyLabel.from_string(lbl_str, separator))
        current_words.append(word)
        current_postags.append(postag)

    return token_list_counter, labels_counter
