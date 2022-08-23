from models.dependency_label import DependencyLabel
from models.conll_node import ConllNode
from encs.enc_deps import *
from utils.constants import *
from utils.reader import parse_conllu
from heuristics.heur_deps import postprocess_tree

# Encoding
def encode_dependencies(in_path, out_path, separator, encoding_type, displacement, planar_alg, features):
    '''
    Encodes the selected file according to the specified parameters:
    :param in_path: Path of the file to be encoded
    :param out_path: Path where to write the encoded labels
    :param encoding_type: Encoding used
    :param separator: string used to separate label fields
    :param displacement: boolean to indicate if use displacement in bracket based encodings
    :param planar_alg: string used to choose the plane separation algorithm
    :param features: features to add as columns to the labels file
    '''

    # Create the encoder
    if encoding_type == D_ABSOLUTE_ENCODING:
            encoder = D_NaiveAbsoluteEncoding(separator)
    if encoding_type == D_RELATIVE_ENCODING:
            encoder = D_NaiveRelativeEncoding(separator)
    if encoding_type == D_POS_ENCODING:
            encoder = D_PosBasedEncoding(separator)
    if encoding_type == D_BRACKET_ENCODING:
            encoder = D_BrkBasedEncoding(separator, displacement)
    if encoding_type == D_BRACKET_ENCODING_2P:
            encoder = D_Brk2PBasedEncoding(separator, displacement, planar_alg)

    # Open Files
    f_in=open(in_path)
    f_out=open(out_path,"w+")
    
    # Read Features
    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    tree_counter = 0
    label_counter = 0

    conll_node_list = parse_conllu(f_in)
    label_set = set()
    
    for node_list in conll_node_list:
        # encode labels
        encoded_labels = encoder.encode(node_list)
        
        # append BOS to tree
        linearized_tree=[]
        linearized_tree.append(u"\t".join(([BOS] * (3 + (1+len(features) if features else 0)))))
        
        # clear dummy root
        node_list = node_list[1:]

        # append labels to tree
        for n, l in zip(node_list, encoded_labels):
            # append the label to a set to count different labels
            label_set.add(l)

            # append word and postag
            output_line = [n.form, n.upos]

            # append features
            if features:
                output_line.append(n.lemma)
                f_list = ["_"] * len(features)
                af = n.feats.split("|")
                for element in af:
                    key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                    if key in f_idx_dict.keys():
                        f_list[f_idx_dict[key]] = value
                
                for element in f_list:
                    output_line.append(element)
            
            # append label
            output_line.append(str(l))

            linearized_tree.append(u"\t".join(output_line))

        # append EOS to tree
        linearized_tree.append(u"\t".join(([EOS] * (3 + (1+len(features) if features else 0)))))

        # write tree
        for row in linearized_tree:
            label_counter+=1
            f_out.write(row+'\n')

        f_out.write("\n")
        tree_counter+=1
    
    return tree_counter, label_counter, len(label_set)

# Decoding
def decode_dependencies(in_path, out_path, separator, encoding_type, displacement, multiroot, root_search):
    '''
    Decodes the selected file according to the specified parameters:
    :param in_path: Path of the file to be encoded
    :param out_path: Path where to write the encoded labels
    :param encoding_type: Encoding used
    :param separator: string used to separate label fields
    :param displacement: boolean to indicate if use displacement in bracket based encodings
    :param multiroot: boolean to indicate if multiroot conll trees are allowed
    :param root_search: strategy to select how to search the root if no root found in decoded tree
    '''

    if encoding_type == D_ABSOLUTE_ENCODING:
            decoder = D_NaiveAbsoluteEncoding(separator)
    if encoding_type == D_RELATIVE_ENCODING:
            decoder = D_NaiveRelativeEncoding(separator)
    if encoding_type == D_POS_ENCODING:
            decoder = D_PosBasedEncoding(separator)
    if encoding_type == D_BRACKET_ENCODING:
            decoder = D_BrkBasedEncoding(separator, displacement)
    if encoding_type == D_BRACKET_ENCODING_2P:
            decoder = D_Brk2PBasedEncoding(separator, displacement)

    f_in=open(in_path)
    f_out=open(out_path,"w+")

    token_list_counter=0
    labels_counter=0

    current_labels = []
    current_words = []
    current_postags = []

    for line in f_in: 

        if BOS in line:
            # Begin of Sentence: Reset Lists
            current_labels=[]
            current_words=[]
            current_postags=[]

            continue

        if EOS in line:
            # End of Sentence: Decode and Write
            sentence = "# text = "+" ".join(current_words)+'\n'
            decoded_conllu = decoder.decode(current_labels, current_postags, current_words)
            postprocess_tree(decoded_conllu, root_search, multiroot)
            
            f_out.write(sentence)
            for l in decoded_conllu:
                f_out.write(str(l))
            f_out.write('\n')

            token_list_counter+=1
            continue

        labels_counter+=1

        line = line.replace('\n','')
        split_line = line.split('\t')
        
        if len(split_line)<=1:
            continue
        if len(split_line) == 2:
            word, lbl_str = split_line
            postag = ""
        else:
            word = split_line[0]
            postag = split_line[1]
            lbl_str = split_line[-1]

        current_labels.append(DependencyLabel.from_string(lbl_str, separator))
        current_words.append(word)
        current_postags.append(postag)

    return token_list_counter, labels_counter
