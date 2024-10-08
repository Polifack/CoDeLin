from codelin.models.linearized_tree import LinearizedTree
from codelin.encs.enc_const import *
from codelin.utils.extract_feats import extract_features_const
from codelin.utils.constants import C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING, C_TETRA_ENCODING, C_JUXTAPOSED_ENCODING, C_GAPS_ENCODING

import stanza.pipeline
from codelin.models.const_tree import C_Tree


## Encoding and decoding

def encode_constituent(in_path, out_path, encoding_type, reverse, separator, multitask, n_label_cols, unary_joiner, features, binary, binary_direction, 
                       binary_marker, traverse_dir, gap_mode, ignore_postags):
    '''
    Encodes the selected file according to the specified parameters:
    :param in_path: Path of the file to be encoded
    :param out_path: Path where to write the encoded labels
    :param encoding_type: Encoding used
    :param separator: string used to separate label fields
    :param unary_joiner: string used to separate nodes from unary chains
    :param features: features to add as columns to the labels file
    '''

    if encoding_type == C_ABSOLUTE_ENCODING:
        encoder = C_NaiveAbsoluteEncoding(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_RELATIVE_ENCODING:
        encoder = C_NaiveRelativeEncoding(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_DYNAMIC_ENCODING:
        encoder = C_NaiveDynamicEncoding(separator, unary_joiner, reverse, binary,  binary_direction, binary_marker)
    elif encoding_type == C_TETRA_ENCODING:
        encoder = C_Tetratag(separator, unary_joiner, traverse_dir, binary_marker)
    elif encoding_type == C_GAPS_ENCODING:
        encoder = C_GapsEncoding(separator, unary_joiner, binary_direction, reverse, binary_marker, gap_mode)
    elif encoding_type == C_JUXTAPOSED_ENCODING:
        encoder = C_JuxtaposedEncoding(separator, unary_joiner, binary, binary_direction, binary_marker)

    else:
        raise Exception("Unknown encoding type")

    # build feature index dictionary
    f_idx_dict = {}
    if features:
        if features == ["ALL"]:
            features = extract_features_const(in_path)
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    file_out = open(out_path, "w", encoding='utf-8')
    file_in = open(in_path, "r", encoding='utf-8')

    tree_counter = 0
    labels_counter = 0
    label_set = set()

    for line in file_in:
        line = line.rstrip()
        tree = C_Tree.from_string(line)

        if ignore_postags:
            tree.set_dummy_preterminals()
        
        linearized_tree = encoder.encode(tree)
        file_out.write(linearized_tree.to_string(f_idx_dict, separate_columns=multitask, n_label_cols=n_label_cols))
        file_out.write("\n")
        tree_counter += 1
        labels_counter += len(linearized_tree)
        for lbl in linearized_tree.labels:
            label_set.add(str(lbl))   
    
    return labels_counter, tree_counter, len(label_set)

def decode_constituent(in_path, out_path, encoding_type, reverse, separator,  multitask, n_label_cols, unary_joiner, conflicts, nulls, postags, lang, binary, 
                       binary_marker, traverse_dir, gap_mode):
    '''
    Decodes the selected file according to the specified parameters:
    :param in_path: Path of the labels file to be decoded
    :param out_path: Path where to write the decoded tree
    :param encoding_type: Encoding used
    :param separator: string used to separate label fields
    :param unary_joiner: string used to separate nodes from unary chains
    :param conflicts: conflict resolution heuristics to apply
    '''

    if encoding_type == C_ABSOLUTE_ENCODING:
        decoder = C_NaiveAbsoluteEncoding(separator, unary_joiner, reverse, binary, None, binary_marker)
    elif encoding_type == C_RELATIVE_ENCODING:
        decoder = C_NaiveRelativeEncoding(separator, unary_joiner, reverse, binary, None, binary_marker)
    elif encoding_type == C_DYNAMIC_ENCODING:
        decoder = C_NaiveDynamicEncoding(separator, unary_joiner, reverse, binary, None, binary_marker)
    elif encoding_type == C_GAPS_ENCODING:
        decoder = C_GapsEncoding(separator, unary_joiner, None, reverse, binary_marker, gap_mode)
    elif encoding_type == C_TETRA_ENCODING:
        decoder = C_Tetratag(separator, unary_joiner, traverse_dir, binary_marker)
    elif encoding_type == C_JUXTAPOSED_ENCODING:
        decoder = C_JuxtaposedEncoding(separator, unary_joiner, binary, None, binary_marker)
    else:
        raise Exception("Unknown encoding type")

    if postags:
        stanza.download(lang=lang)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize, pos')

    f_in = open(in_path)
    f_out = open(out_path,"w+")
    
    tree_string   = ""
    labels_counter = 0
    tree_counter = 0

    for line in f_in:
        if line == "\n":
            tree_string = tree_string.rstrip()
            current_tree = LinearizedTree.from_string(tree_string, mode="CONST", separator=separator, unary_joiner=unary_joiner, separate_columns=multitask, ignore_postags=True, n_label_cols=n_label_cols)
            
            if postags:
                c_tags = nlp(current_tree.get_sentence())
                current_tree.set_postags([word.pos for word in c_tags])
            
            decoded_tree = decoder.decode(current_tree)
            decoded_tree = decoded_tree.postprocess_tree(conflicts, nulls)
            
            tree_string = str(decoded_tree).replace('\n','')+'\n'
            f_out.write(tree_string)
            
            tree_string   = ""
            tree_counter+=1
        tree_string += line
        labels_counter += 1
    
    return tree_counter, labels_counter