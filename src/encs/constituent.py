from src.models.const_label import ConstituentLabel
from src.encs.enc_const import *
from src.utils.constants import EOS, BOS, C_ABSOLUTE_ENCODING, C_RELATIVE_ENCODING, C_DYNAMIC_ENCODING, C_NO_POSTAG_LABEL

import stanza.pipeline
from src.models.const_tree import ConstituentTree


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

    if encoding_type == C_ABSOLUTE_ENCODING:
            encoder = C_NaiveAbsoluteEncoding(separator, unary_joiner)
    if encoding_type == C_RELATIVE_ENCODING:
            encoder = C_NaiveRelativeEncoding(separator, unary_joiner)
    if encoding_type == C_DYNAMIC_ENCODING:
            encoder = C_NaiveDynamicEncoding(separator, unary_joiner)

    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    file_out = open(out_path, "w")
    file_in = open(in_path, "r")

    tree_counter=0
    labels_counter=0
    label_set = set()

    for line in file_in:
        line = line.rstrip()
        tree = ConstituentTree.from_string(line)

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
            file_out.write(str(row)+'\n')
        
        file_out.write("\n")
        tree_counter+=1
    
    return labels_counter, tree_counter, len(label_set)

def decode_constituent(in_path, out_path, encoding_type, separator, unary_joiner, conflicts, nulls, postags, lang):
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

    f_in=open(in_path)
    
    encoded_constituent_trees = []
    current_tree = []
    
    # read the trees
    for line in f_in:
        # skip empty line
        if len(line)<=1:
            continue

        # Separate the label file into columns
        line_columns = line.split("\t") if ("\t") in line else line.split(" ")
        word = line_columns[0]

        if BOS == word:
            current_tree=[]
            continue
        
        if EOS == word:
            encoded_constituent_trees.append(current_tree)
            continue

        if len(line_columns) == 2:
            word, label = line_columns
            postag = C_NO_POSTAG_LABEL
        else:
            word, postag, label = line_columns[0], line_columns[1], line_columns[-1]
        
        # check for bad predictions. hang from root.
        if BOS in label or EOS in label:
            label = "1"+separator+"ROOT"

        current_tree.append([word, postag, ConstituentLabel.from_string(label, separator, unary_joiner)])

    # encode the trees
    
    f_out=open(out_path,"w+")

    if postags:
        stanza.download(lang=lang)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos')
    tree_counter = 0
    labels_counter = 0
    for tree in encoded_constituent_trees:
        current_postags = None
        
        # generate postags if needed
        if postags:
            sentence=""
            for element in tree:
                word = element[0]
                sentence +=" "+word
            doc=nlp(sentence)
            postags = [word.pos for sent in doc.sentences for word in sent.words]
            for line, postag in zip(tree, postags):
                line[1] = postag
        
        decoded_tree = decoder.decode(tree)
        
        # check if null tree obtained during decoding
        if decoded_tree == None:
            final_tree = ConstituentTree.empty_tree()
        else:
            decoded_tree.postprocess_tree(conflicts, nulls)
            final_tree = decoded_tree
            if "-NONE-" in str(final_tree):
                print("has nones:"+" ".join(decoded_tree.get_words()))

        f_out.write(str(final_tree).replace('\n','')+'\n')

        tree_counter+=1
        labels_counter+=len(tree)


    return tree_counter, labels_counter