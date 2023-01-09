import stanza
from src.models.deps_label import DependencyLabel
from src.encs.enc_deps import *
from src.utils.constants import *
from src.models.deps_tree import DependencyTree

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
    
    # Read Features
    if features:
        f_idx_dict = {}
        i=0
        for f in features:
            f_idx_dict[f]=i
            i+=1

    tree_counter = 0
    label_counter = 0


    trees = DependencyTree.read_conllu_file(in_path, filter_projective=False)
    f_out = open(out_path,"w+")
    label_set = set()
    
    for t in trees:
        # encode labels
        encoded_labels = encoder.encode(t)
        
        # append BOS to tree
        linearized_tree=[]
        linearized_tree.append(u"\t".join(([BOS] * (3 + (1+len(features) if features else 0)))))

        # append labels to tree
        for n, l in zip(t, encoded_labels):
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
def decode_dependencies(in_path, out_path, separator, encoding_type, displacement, planar, multiroot, root_search, postags, lang):
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
        decoder = D_Brk2PBasedEncoding(separator, displacement, planar)

    f_in=open(in_path)
    f_out=open(out_path,"w+")

    token_list_counter=0
    labels_counter=0

    current_labels = []
    current_words = []
    current_postags = []

    if postags:
        stanza.download(lang=lang)
        nlp = stanza.Pipeline(lang=lang, processors='tokenize,pos')

    for line in f_in: 
        # split the line and get word/label
        line = line.replace('\n','')

        line_splitter = '\t' if '\t' in line else ' '
        split_line = line.split(line_splitter)
        
        if len(split_line)<=1:
            continue
        
        word = split_line[0]
        lbl_str = split_line[-1]
        
        # check for postags in label
        if len(split_line) == 2:
            postag = ""
        else:
            postag = split_line[1]

        # parse
        if BOS == word:
            # Begin of Sentence: Reset Lists
            current_labels=[]
            current_words=[]
            current_postags=[]

            continue

        if EOS == word:
            # End of Sentence: Decode and Write
            sentence = " ".join(current_words)
            if postags:
                doc=nlp(sentence)
                current_postags = [word.pos for sent in doc.sentences for word in sent.words]
            sentence = "# text = "+sentence+'\n'

            # decode and postprocess
            decoded_conllu = decoder.decode(current_labels, current_postags, current_words)
            decoded_conllu.postprocess_tree(root_search, multiroot)

            # write
            DependencyTree.write_conllu(f_out, decoded_conllu)

            token_list_counter+=1
            continue

        labels_counter+=1

        # check for bad predicted label as -bos- or -eos-
        if lbl_str == BOS or lbl_str == EOS:
            lbl_str = D_NONE_LABEL+separator+"0"

        # append labels
        current_labels.append(DependencyLabel.from_string(lbl_str, separator))
        current_words.append(word)
        current_postags.append(postag)

    return token_list_counter, labels_counter
