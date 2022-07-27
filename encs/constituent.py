from models.constituent_label import ConstituentLabel
from encs.enc_const import *
from utils.constants import EOS, BOS, C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING
from utils.reader import parse_constituent_labels
from heuristics.heur_const import postprocess_tree

from stanza.models.constituency.parse_tree import Tree
from stanza.models.constituency.tree_reader import read_trees, read_tree_file

import stanza.pipeline
import copy
import re


## Encoding and decoding

def encode_constituent(in_path, out_path, encoding_type, separator, unary_joiner, features):
    '''
    Encodes the selected file according to the specified parameters:
    :param in_path: Path of the file to be encoded
    :param out_path: Path where to write the encoded labels
    :param encoding_type: Encoding used
    :param separator: string used to separate label fields
    :param unary_joiner: string used to separate nodes from unary chains
    :param features: features to add as columns to the labels file
    '''

    trees=read_tree_file(in_path)
    f_out=open(out_path,"w+")

    if encoding_type == C_ABSOLUTE_ENCODING:
            encoder = C_NaiveAbsoluteEncoding(separator, unary_joiner)
    if encoding_type == C_RELATIVE_ENCODING:
            encoder = C_NaiveRelativeEncoding(separator, unary_joiner)
    if encoding_type == C_DYNAMIC_ENCODING:
            encoder = C_NaiveDynamicEncoding(separator, unary_joiner)
    
    tree_counter=0
    labels_counter=0
    label_set = set()

    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    for tree in trees:
        words, pos_tags, labels, additional_feats = encoder.encode(tree)
        linearized_tree=[]

        linearized_tree.append(u"\t".join(([BOS] * (3 + (len(features) if features else 0)))))

        for l, p, w, af in zip(labels, pos_tags, words, additional_feats):
            # create the output line of the linearized tree
            output_line = [w,p]
            # check for additional information inside the postag label
            if features:
                f_list = ["_"] * len(features)
                if af is not None:
                    for element in af:
                        key, value = element.split("=", 1) if len(element.split("=",1))==2 else (None, None)
                        if key in f_idx_dict.keys():
                            f_list[f_idx_dict[key]] = value
                
                # append the additional elements or the placehodler
                for element in f_list:
                    output_line.append(element)

            # add the label
            label_set.add(str(l))
            output_line.append(str(l))
                                  
            linearized_tree.append(u"\t".join(output_line))
        linearized_tree.append(u"\t".join(([EOS] * (3 + (len(features) if features else 0)))))

        for row in linearized_tree:
            labels_counter+=1
            f_out.write(str(row)+'\n')
        f_out.write("\n")
        tree_counter+=1
    
    return labels_counter, tree_counter, len(label_set)

def decode_constituent(in_path, out_path, encoding_type, separator, unary_joiner, conflicts):
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
            decoder = C_NaiveAbsoluteEncoding(separator, unary_joiner)
    if encoding_type == C_RELATIVE_ENCODING:
            decoder = C_NaiveRelativeEncoding(separator, unary_joiner)
    if encoding_type == C_DYNAMIC_ENCODING:
            decoder = C_NaiveDynamicEncoding(separator, unary_joiner)

    encoded_constituent_trees = parse_constituent_labels(in_path, separator, unary_joiner)

    f_out=open(out_path,"w+")

    tree_counter = 0
    labels_counter = 0
    for tree in encoded_constituent_trees:
        decoded_tree = decoder.decode(tree)
        #print(decoded_tree)
        final_tree = postprocess_tree(decoded_tree, conflicts)
        f_out.write(str(final_tree).replace('\n','')+'\n')

        tree_counter+=1
        labels_counter+=len(tree)


    return tree_counter, labels_counter