import stanza
import copy
from codelin.models.linearized_tree import LinearizedTree
from codelin.models.deps_label import D_Label
from codelin.encs.enc_deps import *
from codelin.utils.constants import *
from codelin.models.deps_tree import D_Tree


def extract_features_deps(in_path):
    feats_list=set()
    trees = D_Tree.read_conllu_file(in_path, filter_projective=False)
    for t in trees:
        for node in t:
            if node.feats != "_":
                feats_list = feats_list.union(a for a in (node.feats.keys()))

    return sorted(feats_list)

# Encoding
def encode_dependencies(in_path, out_path, encoding_type, separator, multitask, displacement, 
                        planar_alg, root_enc, features, sep_bit, add_bos_eos):
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
    elif encoding_type == D_RELATIVE_ENCODING:
            encoder = D_NaiveRelativeEncoding(separator, root_enc)
    elif encoding_type == D_POS_ENCODING:
            encoder = D_PosBasedEncoding(separator)
    elif encoding_type == D_BRACKET_ENCODING:
            encoder = D_BrkBasedEncoding(separator, displacement)
    elif encoding_type == D_BRACKET_ENCODING_2P:
            encoder = D_Brk2PBasedEncoding(separator, displacement, planar_alg)
    elif encoding_type == D_BRK_4B_ENCODING:
            encoder = D_Brk4BitsEncoding(separator) 
    elif encoding_type == D_BRK_7B_ENCODING:
            encoder = D_Brk7BitsEncoding(separator)
    elif encoding_type == D_6TG_ENCODING:
            encoder = D_HexatagEncoding(separator)
    else:
        raise Exception("Unknown encoding type")
    
    f_idx_dict = {}
    if features:
        if features == ["ALL"]:
            features = extract_features_deps(in_path)
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    file_out = open(out_path,"w+")
    label_set = set()
    tree_counter = 0
    label_counter = 0
    trees = D_Tree.read_conllu_file(in_path, filter_projective=False)
    
    for t in trees:
        # encode labels
        linearized_tree = encoder.encode(t)

        if sep_bit:
            for w, p, af, l in linearized_tree.iterrows():
                xi = l.separate_bits(sep_bit)
                l.xi = separator.join(xi)

        file_out.write(linearized_tree.to_string(f_idx_dict, separate_columns=multitask, add_bos_eos=add_bos_eos))
        file_out.write("\n")
        
        tree_counter += 1
        label_counter += len(linearized_tree)
        
        for lbl in linearized_tree.labels:
            label_set.add(str(lbl))      
    
    return tree_counter, label_counter, len(label_set)

# Decoding
def decode_dependencies(in_path, out_path, encoding_type, separator, multitask, displacement, multiroot, root_search, root_enc, postags, lang, sep_bit, count_heur=False):
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
    elif encoding_type == D_RELATIVE_ENCODING:
        decoder = D_NaiveRelativeEncoding(separator, root_enc)
    elif encoding_type == D_POS_ENCODING:
        decoder = D_PosBasedEncoding(separator)
    elif encoding_type == D_BRACKET_ENCODING:
        decoder = D_BrkBasedEncoding(separator, displacement)
    elif encoding_type == D_BRACKET_ENCODING_2P:
        decoder = D_Brk2PBasedEncoding(separator, displacement, None)
    elif encoding_type == D_BRK_4B_ENCODING:
        decoder = D_Brk4BitsEncoding(separator) 
    elif encoding_type == D_BRK_7B_ENCODING:
        decoder = D_Brk7BitsEncoding(separator)
    elif encoding_type == D_6TG_ENCODING:
        decoder = D_HexatagEncoding(separator)
    else:
        raise Exception("Unknown encoding type")

    f_in=open(in_path)
    f_out=open(out_path,"w+")

    tree_counter=0
    labels_counter=0
    heur_counter=0

    tree_string = ""

    if postags:
        stanza.download(lang=lang)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos,lemma')

    for line in f_in:
        if line == "\n":
            tree_string = tree_string.rstrip()
            mode = "DEPS" if encoding_type!=D_6TG_ENCODING else "CONST"
            current_tree = LinearizedTree.from_string(tree_string, mode=mode, separator=separator, separate_columns=multitask)
            if postags:
                print(current_tree)
                c_tags = nlp(current_tree.get_sentence()).sentences                
                c_tags = [w._words for w in c_tags[1:]]
                print(c_tags)
                c_tags = [w for w in c_tags[0]]

                #c_tags = c_tags[0].words
                #c_tags = [t._words for t in c_tags]
                #print(c_tags)
                #c_tags = [t._upos for t in c_tags]
                current_tree.set_postags([word._upos for word in c_tags[1:]])
            
            decoded_tree = decoder.decode(current_tree)
            if count_heur:
                base_tree = copy.deepcopy(decoded_tree)
                decoded_tree.postprocess_tree(root_search, multiroot)
                for n1, n2 in zip(base_tree.nodes, decoded_tree.nodes):
                    if n1 != n2:
                        heur_counter+=1
                        break

            decoded_tree.postprocess_tree(root_search, multiroot)
            f_out.write("# text = "+decoded_tree.get_sentence()+"\n")
            f_out.write(str(decoded_tree))
            
            tree_string = ""
            tree_counter+=1
        
        tree_string += line
        labels_counter += 1


    return tree_counter, labels_counter, heur_counter
